"""Deliberately-broken reference for algorithmic/a07_count_inversions.

Planted defect: naïve O(n²) double-loop counting.

The results are CORRECT for small inputs (all correctness tests pass), but
at n=200 000 this requires ~20 billion comparisons and will time out, causing
the hard complexity-gate test to FAIL.

This demonstrates that the grader enforces the O(n log n) time requirement,
not just correctness.
"""
from __future__ import annotations


def count_inversions(nums: list[int]) -> int:
    """Return the number of inversion pairs (i, j) with i < j and nums[i] > nums[j].

    Equal elements are NOT considered an inversion.

    BUG: naïve O(n²) double loop — correct on small inputs but times out
    on the large-input complexity gate (n=200 000).
    """
    count = 0
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] > nums[j]:
                count += 1
    return count
