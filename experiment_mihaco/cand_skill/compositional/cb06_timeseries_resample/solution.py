"""
Compositional 06 — timeseries_resample
Resample irregular sensor readings onto a regular grid, interpolate interior gaps,
and flag outliers via scipy z-score.
"""

import numpy as np
import pandas as pd
from scipy.stats import zscore


def resample_clean(readings: list[dict], freq: str) -> dict:
    """
    Resample irregular sensor readings onto a regular grid defined by `freq`,
    interpolate interior NaN gaps, and flag outliers.

    Parameters
    ----------
    readings : list[dict]
        Each dict has keys 'ts' (ISO-8601 str) and 'value' (float, may be NaN).
    freq : str
        A valid pandas offset alias, e.g. "1min", "5min", "1h".

    Returns
    -------
    dict with keys: index, values, outliers, n_interpolated, mean, std

    Raises
    ------
    ValueError
        If readings is empty, any ts cannot be parsed, or freq is invalid.
    """
    # Step 1: Guard — empty readings
    if not readings:
        raise ValueError("readings must not be empty")

    # Step 1: Parse timestamps and extract values
    ts_list = []
    val_list = []
    for r in readings:
        try:
            ts_parsed = pd.Timestamp(r["ts"])
            if ts_parsed is pd.NaT:
                raise ValueError(f"Cannot parse timestamp: {r['ts']!r}")
        except Exception as exc:
            raise ValueError(f"Cannot parse timestamp: {r['ts']!r}") from exc
        ts_list.append(ts_parsed)
        val_list.append(float(r["value"]) if not (r["value"] != r["value"]) else float("nan"))

    # Check for NaT after bulk parsing (redundant safety net)
    dti = pd.DatetimeIndex(ts_list)
    if dti.isna().any():
        raise ValueError("One or more timestamps could not be parsed.")

    # Step 2: Build Series, sort ascending
    s = pd.Series(val_list, index=dti, dtype=float)
    s = s.sort_index()

    # Step 3: Drop duplicate timestamps, keeping LAST occurrence
    s = s[~s.index.duplicated(keep="last")]

    # Step 4: Series is built (already done above)

    # Step 5: Resample to freq, taking mean of each bucket
    try:
        resampled = s.resample(freq).mean()
    except Exception as exc:
        raise ValueError(f"Invalid freq alias {freq!r}: {exc}") from exc

    # Validate freq produced a non-empty result (extra safety)
    if resampled.empty:
        raise ValueError(f"Resampling with freq={freq!r} produced an empty result.")

    # Step 6: Record NaN positions before interpolation, then interpolate interior only
    nan_before = resampled.isna()
    resampled_interp = resampled.interpolate(method="linear", limit_area="inside")
    n_interpolated = int((nan_before & resampled_interp.notna()).sum())

    # Step 7: Compute outlier flags using scipy z-score
    arr = resampled_interp.values.astype(float)
    z_scores = zscore(arr, nan_policy="omit")

    outliers = []
    for z_val in z_scores:
        if np.isnan(z_val):
            outliers.append(False)
        else:
            outliers.append(bool(abs(z_val) > 3.0))

    # Step 8: Compute mean and std over non-NaN cleaned values
    valid_count = int(np.sum(~np.isnan(arr)))
    if valid_count == 0:
        # All buckets are still NaN — return NaN statistics
        mean_val = float("nan")
        std_val = float("nan")
    elif valid_count == 1:
        # Only one non-NaN value: mean is well-defined, std with ddof=1 is NaN
        mean_val = float(np.nanmean(arr))
        std_val = float("nan")
    else:
        mean_val = float(np.nanmean(arr))
        std_val = float(np.nanstd(arr, ddof=1))

    # Build return dict
    index_list = [ts.isoformat() for ts in resampled_interp.index]
    values_list = [None if np.isnan(v) else float(v) for v in arr]

    return {
        "index": index_list,
        "values": values_list,
        "outliers": outliers,
        "n_interpolated": n_interpolated,
        "mean": mean_val,
        "std": std_val,
    }
