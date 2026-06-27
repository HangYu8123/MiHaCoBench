"""
Streaming covariance using Welford's online algorithm for numerical stability.
"""
import collections.abc
import math
import numpy as np


def streaming_stats(pairs: collections.abc.Iterable[tuple[float, float]]) -> dict:
    """
    Consume pairs exactly once and return streaming statistics.

    Uses Welford's online algorithm for numerically stable single-pass computation
    of mean, variance, and covariance even with large constant offsets.
    """
    n = 0
    mean_x = 0.0
    mean_y = 0.0
    # Welford accumulators:
    # M2_x = sum of (x_i - mean_x)^2 (accumulated via old/new mean deltas)
    # M2_y = sum of (y_i - mean_y)^2
    # C    = sum of cross-deviations (for covariance)
    M2_x = 0.0
    M2_y = 0.0
    C = 0.0

    for x, y in pairs:
        n += 1
        # Compute deltas BEFORE updating means
        dx_old = x - mean_x
        dy_old = y - mean_y

        mean_x += dx_old / n
        mean_y += dy_old / n

        # Deltas AFTER updating means
        dx_new = x - mean_x
        dy_new = y - mean_y

        # Welford update: M2 += old_delta * new_delta
        M2_x += dx_old * dx_new
        M2_y += dy_old * dy_new

        # Covariance accumulator: C += old_dx * new_dy (or equivalently old_dy * new_dx)
        # Standard Chan/Welford: C += (x - old_mean_x) * (y - new_mean_y)
        C += dx_old * dy_new

    if n == 0:
        raise ValueError("pairs is empty: cannot compute statistics")

    var_x = M2_x / n
    var_y = M2_y / n
    cov = C / n

    # Use numpy to assemble the result vector (surface-form requirement)
    result_array = np.array([float(n), mean_x, mean_y, var_x, var_y, cov])

    # Pearson correlation
    denom = math.sqrt(float(result_array[3]) * float(result_array[4]))
    if denom == 0.0:
        corr = 0.0
    else:
        corr = float(result_array[5]) / denom

    return {
        "n": int(result_array[0]),
        "mean_x": float(result_array[1]),
        "mean_y": float(result_array[2]),
        "var_x": float(result_array[3]),
        "var_y": float(result_array[4]),
        "cov": float(result_array[5]),
        "corr": float(corr),
    }
