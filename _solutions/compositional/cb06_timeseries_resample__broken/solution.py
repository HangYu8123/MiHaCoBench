"""BROKEN reference for compositional/cb06_timeseries_resample.

PLANTED DEFECT (localized, NaN-handling): the outlier z-scores and the summary
statistics are computed *without* NaN-awareness:

  * ``scipy.stats.zscore`` is called with the default ``nan_policy="propagate"``
    instead of ``"omit"``.
  * ``numpy.mean`` / ``numpy.std`` are used instead of ``numpy.nanmean`` /
    ``numpy.nanstd``.

When the cleaned series contains a leading (or trailing) empty bucket that
interior-only interpolation legitimately leaves as NaN, a single NaN propagates:
EVERY z-score becomes NaN (so no outlier is ever flagged, including a real
spike), and ``mean`` / ``std`` come back as NaN.

Everything else (parsing, sorting, dedup, resample, interpolation count) is
correct, so the module imports and runs cleanly — only specific tests fail.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import scipy.stats


def resample_clean(readings: list[dict], freq: str) -> dict:
    """Resample irregular readings onto a regular grid and flag outliers.

    See the gold reference / TASK.md for the full contract.

    Raises
    ------
    ValueError
        If ``readings`` is empty, a ``ts`` is unparseable, or ``freq`` is invalid.
    """
    if not isinstance(readings, list) or len(readings) == 0:
        raise ValueError("readings must be a non-empty list")

    try:
        ts = pd.to_datetime([r["ts"] for r in readings], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"unparseable timestamp: {exc}") from exc

    values = [float(r["value"]) for r in readings]
    series = pd.Series(values, index=pd.DatetimeIndex(ts))

    series = series.sort_index()
    series = series[~series.index.duplicated(keep="last")]

    try:
        resampled = series.resample(freq).mean()
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid freq {freq!r}: {exc}") from exc

    nan_before = resampled.isna().to_numpy()
    filled = resampled.interpolate(method="linear", limit_area="inside")
    nan_after = filled.isna().to_numpy()
    n_interpolated = int(np.sum(nan_before & ~nan_after))

    cleaned = filled.to_numpy(dtype=float)

    # BUG: default nan_policy="propagate" -> a single NaN makes every z NaN.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        z = np.asarray(scipy.stats.zscore(cleaned), dtype=float)
    outliers = [bool(np.isfinite(zz) and abs(zz) > 3.0) for zz in z]

    # BUG: not NaN-aware -> a single NaN makes mean/std NaN.
    n_valid = int(np.count_nonzero(~np.isnan(cleaned)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mean = float(np.mean(cleaned)) if n_valid >= 1 else float("nan")
        std = float(np.std(cleaned, ddof=1)) if n_valid >= 2 else float("nan")

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
