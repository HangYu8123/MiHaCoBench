"""Broken reference for compositional/cb09_streaming_covariance.

PLANTED DEFECT (the textbook numerical trap): accumulate raw power sums
(sum x, sum y, sum x^2, sum y^2, sum x*y) in one pass and compute

    var_x = mean(x^2) - mean(x)^2
    cov   = mean(x*y) - mean(x)*mean(y)

at the end. Algebraically correct, but it subtracts two enormous, nearly-equal
floating-point numbers. When the data has a large offset (values ~1e9, true
variance ~100) the leading ~1e18 magnitudes cancel and the result is dominated by
float64 rounding error — variances come out hundreds off (sometimes negative).
The interface and the small-magnitude behaviour are identical to the gold, so the
defect only surfaces on the large-offset adversarial stream.
"""
from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np


def streaming_stats(pairs: Iterable[tuple[float, float]]) -> dict:
    """BROKEN: naive sum-of-squares formula (catastrophic cancellation)."""
    n = 0
    sx = 0.0
    sy = 0.0
    sxx = 0.0
    syy = 0.0
    sxy = 0.0

    for x, y in pairs:
        x = float(x)
        y = float(y)
        n += 1
        sx += x
        sy += y
        sxx += x * x
        syy += y * y
        sxy += x * y

    if n == 0:
        raise ValueError("streaming_stats requires at least one (x, y) pair")

    mean_x = sx / n
    mean_y = sy / n
    var_x = sxx / n - mean_x * mean_x  # BUG: catastrophic cancellation on large offset
    var_y = syy / n - mean_y * mean_y
    cov = sxy / n - mean_x * mean_y
    if var_x == 0.0 or var_y == 0.0:
        corr = 0.0
    else:
        corr = cov / math.sqrt(var_x * var_y)

    vec = np.array([mean_x, mean_y, var_x, var_y, cov, corr], dtype=float)
    return {
        "n": n,
        "mean_x": float(vec[0]),
        "mean_y": float(vec[1]),
        "var_x": float(vec[2]),
        "var_y": float(vec[3]),
        "cov": float(vec[4]),
        "corr": float(vec[5]),
    }
