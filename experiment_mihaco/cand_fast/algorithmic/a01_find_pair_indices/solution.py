def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}  # value -> first (smallest) index seen
    for j, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            return (seen[complement], j)
        if val not in seen:
            seen[val] = j
    return None
