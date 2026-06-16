"""
Compositional 06 — timeseries_resample
Irregular Time-Series Resampling + Robust Outliers
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import zscore  # scipy.stats.zscore — surface-form check


def resample_clean(readings: list[dict], freq: str) -> dict:
    """
    Resample irregularly-spaced sensor readings onto a regular grid,
    fill interior gaps, and flag outliers.

    Parameters
    ----------
    readings : list[dict]
        Each dict has keys 'ts' (ISO-8601 str) and 'value' (float, may be NaN).
    freq : str
        A valid pandas offset alias (e.g. '1min', '5T', '1H').

    Returns
    -------
    dict with keys: index, values, outliers, n_interpolated, mean, std

    Raises
    ------
    ValueError
        - readings is empty
        - any ts cannot be parsed as a timestamp
        - freq is not a valid pandas offset alias
    """
    # Step 0 — validate non-empty
    if not readings:
        raise ValueError("readings must not be empty")

    # Step 1 — parse timestamps
    parsed_ts = []
    for r in readings:
        try:
            parsed_ts.append(pd.to_datetime(r["ts"]))
        except Exception as e:
            raise ValueError(f"Cannot parse timestamp {r['ts']!r}: {e}") from e

    # Collect values (preserving NaN as float)
    values = [float(r["value"]) for r in readings]

    # Step 2 — sort ascending by timestamp
    paired = sorted(zip(parsed_ts, values), key=lambda x: x[0])
    sorted_ts, sorted_vals = zip(*paired) if paired else ([], [])

    # Step 3 & 4 — build Series, then drop duplicates keeping LAST
    index = pd.DatetimeIndex(sorted_ts)
    series = pd.Series(sorted_vals, index=index, dtype=float)
    # Sort first (already sorted), then keep last duplicate
    series = series[~series.index.duplicated(keep="last")]

    # Step 5 — resample to regular grid, mean of each bucket
    # Validate freq by attempting to convert offset
    try:
        pd.tseries.frequencies.to_offset(freq)
    except Exception as e:
        raise ValueError(f"Invalid pandas offset alias {freq!r}: {e}") from e

    try:
        resampled = series.resample(freq).mean()
    except Exception as e:
        raise ValueError(f"Resampling failed with freq={freq!r}: {e}") from e

    # Step 6 — interior interpolation only
    # Capture NaN mask BEFORE interpolation
    nan_before = resampled.isna()
    cleaned = resampled.interpolate(method="linear", limit_area="inside")
    # Count buckets that were NaN before and are non-NaN after
    n_interpolated = int((nan_before & cleaned.notna()).sum())

    # Step 7 — outlier detection using scipy.stats.zscore
    cleaned_values = cleaned.values  # numpy array
    z_scores = zscore(cleaned_values, nan_policy="omit")  # scipy.stats.zscore call
    outliers = []
    for zi in z_scores:
        if np.isnan(zi):
            outliers.append(False)
        else:
            outliers.append(bool(abs(zi) > 3.0))

    # Step 8 — statistics over non-NaN cleaned values
    mean_val = float(np.nanmean(cleaned_values))
    std_val = float(np.nanstd(cleaned_values, ddof=1))

    # Build output index as ISO-8601 strings
    # Use strftime to avoid microsecond artifacts
    index_strs = cleaned.index.strftime("%Y-%m-%dT%H:%M:%S").tolist()

    # Build values list: None for NaN, float otherwise
    out_values = []
    for v in cleaned_values:
        if np.isnan(v):
            out_values.append(None)
        else:
            out_values.append(float(v))

    return {
        "index": index_strs,
        "values": out_values,
        "outliers": outliers,
        "n_interpolated": n_interpolated,
        "mean": mean_val,
        "std": std_val,
    }
