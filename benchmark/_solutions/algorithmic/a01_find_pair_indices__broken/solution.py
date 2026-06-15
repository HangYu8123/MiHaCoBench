"""Deliberately-broken reference for algorithmic/a01_find_pair_indices.

Planted defect: O(n^2) nested-loop implementation. Produces correct answers
on small inputs but exceeds the 5-second budget on the 2_000_000-element
large-input gate, causing the hard complexity test to fail.
"""
from __future__ import annotations


def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """O(n^2) two-sum — correct but too slow for the large-input gate."""
    n = len(nums)
    for j in range(1, n):
        for i in range(j):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None
