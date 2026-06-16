"""BROKEN reference for algorithmic/a06_sliding_window_median.

Defect: re-sorts each window on every step → O(n*k log k) instead of O(n log k).
Correct on small inputs; TIMES OUT on the hard complexity gate (N=200_000, k=1_000).
"""
from __future__ import annotations


def sliding_window_median(nums: list[float], k: int) -> list[float]:
    """Return the median of every contiguous window of size k.

    BROKEN: naive O(n*k log k) implementation — re-sorts every window.
    Correct for small inputs but times out for large n and k.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    n = len(nums)
    if k > n:
        return []

    result: list[float] = []
    for i in range(n - k + 1):
        window = sorted(nums[i : i + k])
        if k % 2 == 1:
            result.append(float(window[k // 2]))
        else:
            result.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return result
