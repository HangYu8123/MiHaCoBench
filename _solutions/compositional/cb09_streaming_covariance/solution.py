"""Gold reference for compositional/cb09_streaming_covariance.

Single-pass, bounded-memory mean / variance / covariance / correlation over a
stream of ``(x, y)`` pairs, using NUMERICALLY STABLE online updates:

* Welford's algorithm for each mean and its sum-of-squared-deviations ``M2``;
* a running co-moment ``C`` for the covariance.

These accumulate deviations from the *running mean*, so every quantity added is
O(spread) rather than O(value). The naive ``E[x^2] - E[x]^2`` / ``E[xy] -
E[x]E[y]`` formulas instead subtract two huge nearly-equal numbers and lose all
precision when the data has a large offset — this gold avoids that entirely.

The stream is consumed exactly once and only a handful of scalars are retained,
so memory is O(1) regardless of stream length. ``numpy`` assembles the final
result vector.
"""
from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np


def streaming_stats(pairs: Iterable[tuple[float, float]]) -> dict:
    """Return single-pass population statistics over ``pairs``.

    Returns a dict with keys ``n, mean_x, mean_y, var_x, var_y, cov, corr``
    (population variance/covariance, ddof=0). ``corr`` is set to ``0.0`` when
    either variance is ``0`` (undefined). Raises ``ValueError`` on empty input.
    """
    n = 0
    mean_x = 0.0
    mean_y = 0.0
    m2x = 0.0
    m2y = 0.0
    comoment = 0.0

    for x, y in pairs:
        x = float(x)
        y = float(y)
        n += 1
        dx = x - mean_x
        mean_x += dx / n
        m2x += dx * (x - mean_x)
        dy = y - mean_y
        mean_y += dy / n
        m2y += dy * (y - mean_y)
        comoment += dx * (y - mean_y)

    if n == 0:
        raise ValueError("streaming_stats requires at least one (x, y) pair")

    var_x = m2x / n
    var_y = m2y / n
    cov = comoment / n
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
