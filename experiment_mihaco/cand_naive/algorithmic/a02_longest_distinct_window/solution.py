def longest_distinct_window(seq: list[int]) -> int:
    """Return the length of the longest contiguous subarray with all distinct elements."""
    if not seq:
        return 0

    last_seen = {}  # element -> last seen index
    left = 0
    max_len = 0

    for right, val in enumerate(seq):
        if val in last_seen and last_seen[val] >= left:
            left = last_seen[val] + 1
        last_seen[val] = right
        window_len = right - left + 1
        if window_len > max_len:
            max_len = window_len

    return max_len
