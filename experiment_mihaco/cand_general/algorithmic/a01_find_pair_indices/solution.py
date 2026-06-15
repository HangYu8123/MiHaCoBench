from __future__ import annotations


def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return the pair of indices (i, j) with i < j such that nums[i] + nums[j] == target.

    Tiebreaking:
        - Among all valid pairs, return the one with the smallest j.
        - Among all pairs sharing the smallest j, return the one with the smallest i.

    Returns None if no valid pair exists.

    Algorithm: O(n) single-pass hash map.
        - Maintain a dict `seen` mapping value -> smallest index seen so far.
        - For each index j, check whether (target - nums[j]) is already in `seen`.
          If so, return immediately (first hit = smallest j; stored index = smallest i).
        - Insert nums[j] into `seen` only if not already present (preserves smallest i).
        - The complement check precedes insertion, preventing self-pairing when
          target == 2 * nums[j] and only one copy of that value exists.

    Args:
        nums:   List of integers (may contain duplicates; may be empty).
        target: Integer sum to find.

    Returns:
        A tuple (i, j) with i < j on success, or None.
    """
    seen: dict[int, int] = {}  # value -> smallest index seen so far

    for j, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            return (seen[complement], j)
        if val not in seen:
            seen[val] = j

    return None
