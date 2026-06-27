"""
Compositional 06 — timeseries_resample: Irregular Time-Series Resampling + Robust Outliers
"""

import numpy as np
import pandas as pd
from scipy.stats import zscore


def resample_clean(readings: list[dict], freq: str) -> dict:
    """
    Resample irregular time-series readings onto a regular grid, fill interior gaps,
    and flag outliers.

    Parameters
    ----------
    readings : list[dict]
        Each dict has keys 'ts' (ISO-8601 str) and 'value' (float, may be NaN).
    freq : str
        A valid pandas offset alias (e.g. '1min', '5T', 'H').

    Returns
    -------
    dict with keys:
        index          : list[str]   - ISO-8601 timestamps for each bucket
        values         : list[float or None] - cleaned values (None for still-NaN)
        outliers       : list[bool]  - True where abs(z) > 3.0
        n_interpolated : int         - buckets that went from NaN to non-NaN after interpolation
        mean           : float       - nanmean over non-NaN cleaned values
        std            : float       - nanstd(ddof=1) over non-NaN cleaned values

    Raises
    ------
    ValueError : if readings is empty, any ts is unparseable, or freq is invalid.
    """
    # --- Validate inputs ---
    if not readings:
        raise ValueError("readings is empty")

    # Step 1: Parse timestamps
    timestamps = []
    values = []
    for r in readings:
        try:
            ts = pd.Timestamp(r["ts"])
        except Exception:
            raise ValueError(f"Cannot parse timestamp: {r['ts']!r}")
        timestamps.append(ts)
        values.append(r["value"])

    # Step 2 & 3 & 4: Sort, drop duplicates (keep last), build Series
    series = pd.Series(values, index=pd.DatetimeIndex(timestamps), dtype=float)
    series = series.sort_index()
    # Keep last occurrence of each duplicate timestamp
    series = series[~series.index.duplicated(keep="last")]

    # Step 5: Validate freq and resample
    try:
        resampled = series.resample(freq).mean()
    except Exception:
        raise ValueError(f"Invalid pandas offset alias: {freq!r}")

    # Track which buckets are NaN after resampling (before interpolation)
    nan_before = resampled.isna()

    # Step 6: Interpolate interior gaps only
    interpolated = resampled.interpolate(method="linear", limit_area="inside")

    # n_interpolated: buckets that were NaN after resample and non-NaN after interpolate
    nan_after = interpolated.isna()
    n_interpolated = int((nan_before & ~nan_after).sum())

    # Step 7: Compute outlier flags using scipy.stats.zscore
    cleaned_values = interpolated.values  # numpy array
    z_scores = zscore(cleaned_values, nan_policy="omit")

    # A bucket is outlier when abs(z) > 3.0; NaN z-scores are NOT outliers
    outliers = []
    for z in z_scores:
        if z is None or (isinstance(z, float) and np.isnan(z)):
            outliers.append(False)
        else:
            outliers.append(bool(abs(z) > 3.0))

    # Step 8: Compute mean and std over non-NaN cleaned values
    non_nan_vals = cleaned_values[~np.isnan(cleaned_values)]
    if len(non_nan_vals) == 0:
        mean_val = float("nan")
        std_val = float("nan")
    else:
        mean_val = float(np.nanmean(cleaned_values))
        std_val = float(np.nanstd(cleaned_values, ddof=1))

    # Build index as ISO-8601 strings
    index_strs = [ts.isoformat() for ts in interpolated.index]

    # Build values list: float or None
    values_out = []
    for v in cleaned_values:
        if np.isnan(v):
            values_out.append(None)
        else:
            values_out.append(float(v))

    return {
        "index": index_strs,
        "values": values_out,
        "outliers": outliers,
        "n_interpolated": n_interpolated,
        "mean": mean_val,
        "std": std_val,
    }
