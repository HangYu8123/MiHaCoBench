def longest_distinct_window(seq: list[int]) -> int:
    """Return the length of the longest contiguous subarray with all distinct elements.

    Uses a sliding window with a last-seen dict for O(n) time complexity.
    """
    last_seen: dict[int, int] = {}
    left = 0
    max_len = 0

    for right, val in enumerate(seq):
        if val in last_seen:
            left = max(left, last_seen[val] + 1)
        last_seen[val] = right
        max_len = max(max_len, right - left + 1)

    return max_len
