"""
Compositional 06 — timeseries_resample
Resample irregular sensor readings onto a regular grid, fill interior gaps,
and flag outliers using scipy.stats.zscore.
"""

import numpy as np
import pandas as pd
from scipy.stats import zscore


def resample_clean(readings: list[dict], freq: str) -> dict:
    """
    Resample irregular time-series readings to a regular frequency grid,
    interpolate interior gaps, and detect outliers via z-score.

    Parameters
    ----------
    readings : list[dict]
        Each dict has keys 'ts' (ISO-8601 str) and 'value' (float, may be NaN).
    freq : str
        A valid pandas offset alias (e.g. '1min', '5T', 'H').

    Returns
    -------
    dict with keys: index, values, outliers, n_interpolated, mean, std

    Raises
    ------
    ValueError
        If readings is empty, any ts cannot be parsed, or freq is invalid.
    """
    # Step 1: Validate non-empty input
    if not readings:
        raise ValueError("readings must not be empty")

    # Step 2: Parse timestamps
    parsed_rows = []
    for row in readings:
        try:
            ts = pd.to_datetime(row["ts"], format="ISO8601")
        except Exception as exc:
            raise ValueError(f"Cannot parse timestamp: {row['ts']!r}") from exc
        parsed_rows.append({"ts": ts, "value": float(row["value"])})

    # Step 3: Build DataFrame, sort ascending, drop duplicates keeping last
    df = pd.DataFrame(parsed_rows)
    df = df.sort_values("ts")
    df = df.drop_duplicates(subset="ts", keep="last")

    # Step 4: Build Series indexed by DatetimeIndex
    series = pd.Series(df["value"].values, index=pd.DatetimeIndex(df["ts"]))

    # Step 5: Resample to freq using mean; wrap to catch invalid freq alias
    try:
        resampled = series.resample(freq).mean()
    except Exception as exc:
        raise ValueError(f"Invalid pandas offset alias: {freq!r}") from exc

    # Step 6: Snapshot NaN mask before interpolation
    nan_before = resampled.isna()

    # Linearly interpolate interior gaps only (leading/trailing NaN stay NaN)
    cleaned = resampled.interpolate(method="linear", limit_area="inside")

    # Step 7 (n_interpolated): Count buckets that were NaN before and non-NaN after
    nan_after = cleaned.isna()
    n_interpolated = int((nan_before & ~nan_after).sum())

    # Step 8: Compute z-scores using scipy.stats.zscore with nan_policy="omit"
    # nan_policy="omit" returns a SHORTER array (omits NaN positions).
    # We must reconstruct a full-length z array with NaN at the original NaN positions.
    values_arr = cleaned.values.astype(float)
    nan_mask = np.isnan(values_arr)

    if nan_mask.all():
        # All values are NaN — no valid data to compute z-scores
        z_full = np.full(len(values_arr), np.nan)
    elif (~nan_mask).sum() == 1:
        # Only one non-NaN value — z-score is 0.0 for that single value
        z_full = np.full(len(values_arr), np.nan)
        z_full[~nan_mask] = 0.0
    else:
        # Compute z-scores on non-NaN values only (nan_policy="omit" skips NaNs)
        z_omit = zscore(values_arr, nan_policy="omit")
        # z_omit is same length as values_arr when nan_policy="omit" in modern scipy
        # but to be safe, reconstruct from non-NaN positions
        z_full = np.full(len(values_arr), np.nan)
        if len(z_omit) == len(values_arr):
            # Modern scipy: same-length output with NaN at NaN positions
            z_full = z_omit
        else:
            # Older scipy: shorter array — re-insert at non-NaN positions
            z_full[~nan_mask] = z_omit

    # Outlier flag: abs(z) > 3.0, NaN z treated as not outlier
    outliers = [bool(not np.isnan(zi) and abs(zi) > 3.0) for zi in z_full]

    # Step 9: Compute mean and std over non-NaN cleaned values
    non_nan_vals = values_arr[~nan_after.values]
    if len(non_nan_vals) == 0:
        # All buckets are NaN — statistics are NaN
        mean_val = float("nan")
        std_val = float("nan")
    else:
        mean_val = float(np.nanmean(values_arr))
        std_val = float(np.nanstd(values_arr, ddof=1))

    # Step 10: Build return dict
    index_strs = [ts.isoformat() for ts in cleaned.index]
    values_out = [None if np.isnan(v) else float(v) for v in values_arr]

    return {
        "index": index_strs,
        "values": values_out,
        "outliers": outliers,
        "n_interpolated": n_interpolated,
        "mean": mean_val,
        "std": std_val,
    }
