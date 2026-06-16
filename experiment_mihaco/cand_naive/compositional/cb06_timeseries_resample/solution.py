"""
Compositional 06 — timeseries_resample: Irregular Time-Series Resampling + Robust Outliers
"""

import numpy as np
import pandas as pd
from scipy.stats import zscore


def resample_clean(readings: list[dict], freq: str) -> dict:
    """
    Resample irregularly-spaced sensor readings onto a regular grid,
    fill interior gaps, and flag outliers.

    Parameters
    ----------
    readings : list[dict]
        Each dict has keys 'ts' (ISO-8601 str) and 'value' (float, may be NaN).
    freq : str
        A valid pandas offset alias (e.g. '1min', '5min', '1H').

    Returns
    -------
    dict with keys: index, values, outliers, n_interpolated, mean, std

    Raises
    ------
    ValueError
        If readings is empty, any ts cannot be parsed, or freq is invalid.
    """
    # Exception: empty readings
    if not readings:
        raise ValueError("readings is empty")

    # Step 1: Parse timestamps
    timestamps = []
    values = []
    for reading in readings:
        try:
            ts = pd.Timestamp(reading["ts"])
        except Exception:
            raise ValueError(f"Cannot parse timestamp: {reading['ts']!r}")
        timestamps.append(ts)
        values.append(reading["value"])

    # Step 2: Sort by timestamp
    idx = pd.DatetimeIndex(timestamps)
    series = pd.Series(values, index=idx, dtype=float)
    series = series.sort_index()

    # Step 3: Drop duplicate timestamps, keeping LAST occurrence
    series = series[~series.index.duplicated(keep="last")]

    # Step 4: Build Series (already done above)

    # Step 5: Resample to freq, taking MEAN of each bucket
    # Validate freq by attempting to resample
    try:
        resampled = series.resample(freq).mean()
    except Exception as e:
        raise ValueError(f"Invalid freq {freq!r}: {e}")

    # Track which buckets were NaN after resampling (before interpolation)
    nan_after_resample = resampled.isna()

    # Step 6: Linearly interpolate interior gaps only
    interpolated = resampled.interpolate(method="linear", limit_area="inside")

    # Count buckets that were NaN after resample and became non-NaN after interpolation
    nan_after_interpolate = interpolated.isna()
    n_interpolated = int(
        (nan_after_resample & ~nan_after_interpolate).sum()
    )

    # Step 7: Compute outlier flags using scipy.stats.zscore
    cleaned_values = interpolated.values  # numpy array with NaN where still empty

    z_scores = zscore(cleaned_values, nan_policy="omit")

    # A bucket is an outlier when abs(z) > 3.0
    # Buckets where z is NaN are NOT outliers
    outliers = []
    for z in z_scores:
        if z is None or (isinstance(z, float) and np.isnan(z)):
            outliers.append(False)
        elif abs(z) > 3.0:
            outliers.append(True)
        else:
            outliers.append(False)

    # Step 8: Compute mean and std over non-NaN cleaned values
    non_nan_values = cleaned_values[~np.isnan(cleaned_values)]

    if len(non_nan_values) == 0:
        mean_val = float("nan")
        std_val = float("nan")
    else:
        mean_val = float(np.nanmean(cleaned_values))
        std_val = float(np.nanstd(cleaned_values, ddof=1))

    # Build result index (ISO-8601 strings)
    index_strs = [ts.isoformat() for ts in interpolated.index]

    # Build values list (float or None)
    values_list = []
    for v in cleaned_values:
        if np.isnan(v):
            values_list.append(None)
        else:
            values_list.append(float(v))

    return {
        "index": index_strs,
        "values": values_list,
        "outliers": outliers,
        "n_interpolated": n_interpolated,
        "mean": mean_val,
        "std": std_val,
    }
