def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """
    Find two distinct indices i < j such that nums[i] + nums[j] == target.

    Tiebreaking: smallest j first; among ties on j, smallest i.

    Returns (i, j) or None.
    Time complexity: O(n) using a hash map.
    """
    # seen maps value -> list of indices where that value appears (in order)
    # We iterate j from left to right. For each j, we look up (target - nums[j])
    # in seen. If found, the smallest i is seen[complement][0] (earliest index).
    # Because we process j in ascending order, the first valid pair found has
    # the smallest j. Among pairs with the same j, we take the smallest i.

    seen: dict[int, int] = {}  # value -> smallest index seen so far

    for j, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            i = seen[complement]
            return (i, j)
        # Only store the first (smallest) index for each value
        if val not in seen:
            seen[val] = j

    return None
