"""Algorithmic 01 — find_pair_indices: two-sum with tiebreaking.

Finds two distinct indices i < j such that nums[i] + nums[j] == target.
Tiebreaking: smallest j first; among ties on j, smallest i.
Returns (i, j) as a tuple, or None if no valid pair exists.
Time complexity: O(n). Space complexity: O(n).
"""


def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return the pair (i, j) with i < j, nums[i] + nums[j] == target.

    Tiebreaking rule:
      - Among all valid pairs, return the one with the smallest j.
      - Among all pairs sharing that smallest j, return the one with the
        smallest i.

    Parameters
    ----------
    nums:
        List of integers to search.
    target:
        The integer sum to find.

    Returns
    -------
    tuple[int, int] | None
        A tuple (i, j) with i < j on success, or None if no pair exists.
    """
    # seen maps each value to the smallest index at which it appears so far.
    # We check complement before inserting nums[j] to guarantee i != j.
    seen: dict[int, int] = {}

    for j in range(len(nums)):
        complement = target - nums[j]
        if complement in seen:
            # seen[complement] is the smallest i with nums[i] == complement
            # and i < j (because we insert after checking).
            return (seen[complement], j)
        # Only record the first (smallest) index for each value.
        if nums[j] not in seen:
            seen[nums[j]] = j

    return None
