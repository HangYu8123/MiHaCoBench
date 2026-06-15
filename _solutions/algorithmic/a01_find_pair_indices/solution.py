"""Gold reference for algorithmic/a01_find_pair_indices — O(n) two-sum with tiebreaking.

Public contract
---------------
find_pair_indices(nums, target) -> tuple[int, int] | None

Return (i, j) with i < j such that nums[i] + nums[j] == target.
Tiebreak: smallest j first; for equal j, smallest i.
Return None if no such pair exists.

Implementation note
-------------------
Scan left to right; maintain a dict mapping each value to the list of indices
(in ascending order) at which it has appeared. For each position j, check
whether (target - nums[j]) is already in the dict; if so, the smallest such i
is the first entry of that list. Because we scan in order of increasing j, the
first j for which a complement exists is the globally smallest j. We stop
immediately, giving O(n) time and O(n) space.
"""
from __future__ import annotations


def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return (i, j) with i<j, nums[i]+nums[j]==target; tiebreak smallest j then i.

    Returns None if no such pair exists.
    """
    # Maps value -> smallest index seen so far for that value.
    # We only need the *smallest* index, because tiebreaking chooses smallest i
    # for any given j. We record the first occurrence, which is the smallest i.
    seen: dict[int, int] = {}
    for j, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            return (seen[complement], j)
        # Record j only if this value has not been seen before (so seen[v] stays
        # the *first* / smallest index for value v, satisfying the smallest-i rule).
        if val not in seen:
            seen[val] = j
    return None
