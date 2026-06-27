def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return (i, j) with i < j such that nums[i] + nums[j] == target.

    Tiebreaking: smallest j first; among equal j, smallest i.

    O(n) time, O(n) space via a single left-to-right pass with a hash map
    mapping each seen value to the list of all indices at which it appeared.
    """
    # Maps value -> list of indices (in insertion order, i.e. ascending)
    seen: dict[int, list[int]] = {}

    for j, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            # All stored indices are < j; pick the smallest one.
            i = seen[complement][0]  # list is already in ascending order
            return (i, j)
        # Record this index AFTER the complement check (prevents i == j).
        if val not in seen:
            seen[val] = [j]
        else:
            seen[val].append(j)

    return None
