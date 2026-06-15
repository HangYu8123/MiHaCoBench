"""Deliberately-broken reference for algorithmic/a03_window_maxima.

Planted defect: naïve O(n*k) per-window max scan instead of the required O(n)
monotonic-deque approach.  All small-input correctness tests pass, but the
large-input hard-gate test (N=1_000_000, k=1_000, timeout=5s) times out and
fails, proving the grader discriminates against the wrong time complexity.
"""
from __future__ import annotations


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Return the maximum of every contiguous window of size *k* in *nums*.

    BUG: uses O(n*k) brute-force max() on each window — too slow for large N.
    """
    if k <= 0:
        raise ValueError(f"window size k must be >= 1, got {k}")

    n = len(nums)
    if k > n:
        return []

    # O(n*k): recomputes max from scratch for every window — correct but slow.
    return [max(nums[i : i + k]) for i in range(n - k + 1)]
