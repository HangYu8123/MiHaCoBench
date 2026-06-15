"""Algorithmic 01 — find_pair_indices: two-sum with tiebreaking.

Given a list of integers `nums` and an integer `target`, find two distinct
indices i and j (with i < j) such that nums[i] + nums[j] == target.

Tiebreaking rule:
    If multiple valid pairs exist, return the pair with the smallest j.
    Among all pairs sharing that smallest j, return the one with the smallest i.

Complexity: O(n) time using a hash map.
"""


def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """Find two distinct indices i < j such that nums[i] + nums[j] == target.

    Tiebreaking: smallest j first; among equal j, smallest i.
    Uses an O(n) hash-map scan.

    Args:
        nums:   List of integers to search.
        target: The target sum.

    Returns:
        A tuple (i, j) with i < j on success, or None if no valid pair exists.
    """
    if len(nums) < 2:
        return None

    # Map each value seen so far to the SMALLEST index that holds it.
    # We iterate left to right; for each j we want the smallest i < j
    # such that nums[i] == target - nums[j].  By storing only the first
    # (smallest) index for each value we automatically satisfy the
    # tiebreaker "smallest i among pairs with the same j".
    # The tiebreaker "smallest j" is satisfied because we return on the
    # very first j for which a complement exists.
    seen: dict[int, int] = {}  # value -> smallest index seen so far

    for j, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            return (seen[complement], j)
        # Record this index only if the value is not already present
        # (keep the smallest index for each value).
        if val not in seen:
            seen[val] = j

    return None
