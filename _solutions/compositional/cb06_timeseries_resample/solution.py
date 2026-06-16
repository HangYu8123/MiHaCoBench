"""Gold reference for compositional/cb06_timeseries_resample.

Composes pandas (DatetimeIndex + resample + interpolate), numpy (NaN-aware
statistics), and scipy (robust z-scores) to clean an irregular sensor stream.

The defensible NaN-handling choice: leading/trailing empty buckets are left
unfilled (``limit_area="inside"``) and are excluded from every statistic via
``nan_policy="omit"`` / ``numpy.nanmean`` / ``numpy.nanstd``, so a legitimately
empty bucket cannot poison the mean, std, or outlier z-scores.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import scipy.stats


def resample_clean(readings: list[dict], freq: str) -> dict:
    """Resample irregular readings onto a regular grid and flag outliers.

    Parameters
    ----------
    readings : list[dict]
        Each dict has keys ``ts`` (ISO-8601 string) and ``value`` (float, may be
        NaN). Timestamps need not be sorted or unique.
    freq : str
        A pandas offset alias (e.g. ``"1min"``, ``"5min"``, ``"1h"``).

    Returns
    -------
    dict with keys:
        index : list[str]            ISO-8601 timestamp per grid bucket.
        values : list[float | None]  Cleaned value per bucket; None if still NaN.
        outliers : list[bool]        True where abs(zscore) > 3.0.
        n_interpolated : int         Buckets filled by interior interpolation.
        mean : float                 numpy.nanmean over non-NaN cleaned values.
        std : float                  numpy.nanstd(ddof=1) over non-NaN values.

    Raises
    ------
    ValueError
        If ``readings`` is empty, a ``ts`` is unparseable, or ``freq`` is invalid.
    """
    if not isinstance(readings, list) or len(readings) == 0:
        raise ValueError("readings must be a non-empty list")

    # Parse timestamps. pandas raises a ValueError subclass on a bad timestamp.
    try:
        ts = pd.to_datetime([r["ts"] for r in readings], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"unparseable timestamp: {exc}") from exc

    values = [float(r["value"]) for r in readings]
    series = pd.Series(values, index=pd.DatetimeIndex(ts))

    # Sort ascending, then drop duplicate timestamps keeping the LAST.
    series = series.sort_index()
    series = series[~series.index.duplicated(keep="last")]

    # Resample to the regular grid, taking the bucket MEAN. Invalid freq -> error.
    try:
        resampled = series.resample(freq).mean()
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid freq {freq!r}: {exc}") from exc

    # Interior-only interpolation: leading/trailing NaNs stay NaN.
    nan_before = resampled.isna().to_numpy()
    filled = resampled.interpolate(method="linear", limit_area="inside")
    nan_after = filled.isna().to_numpy()
    n_interpolated = int(np.sum(nan_before & ~nan_after))

    cleaned = filled.to_numpy(dtype=float)

    # Robust z-scores over the cleaned values, ignoring still-NaN buckets.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # constant input -> divide-by-zero -> NaN z
        z = np.asarray(scipy.stats.zscore(cleaned, nan_policy="omit"), dtype=float)
    outliers = [bool(np.isfinite(zz) and abs(zz) > 3.0) for zz in z]

    # NaN-aware statistics over the non-NaN cleaned values only.
    n_valid = int(np.count_nonzero(~np.isnan(cleaned)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mean = float(np.nanmean(cleaned)) if n_valid >= 1 else float("nan")
        std = float(np.nanstd(cleaned, ddof=1)) if n_valid >= 2 else float("nan")

    index = [t.isoformat() for t in filled.index]
    out_values = [None if np.isnan(v) else float(v) for v in cleaned]

    return {
        "index": index,
        "values": out_values,
        "outliers": outliers,
        "n_interpolated": n_interpolated,
        "mean": mean,
        "std": std,
    }
