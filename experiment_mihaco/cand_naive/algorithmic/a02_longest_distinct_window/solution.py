def longest_distinct_window(seq: list[int]) -> int:
    """Return the length of the longest contiguous subarray with all distinct elements.

    Uses a sliding window approach with a last-seen map for O(n) time complexity.

    Args:
        seq: A list of integers (may be empty).

    Returns:
        A non-negative integer - the length of the longest contiguous subarray
        with all distinct elements. Returns 0 for an empty list.
    """
    if not seq:
        return 0

    last_seen = {}  # Maps value -> last index seen
    left = 0        # Left boundary of the current window
    max_len = 0     # Maximum window length found so far

    for right, val in enumerate(seq):
        # If we've seen this value before and it's within the current window,
        # move the left pointer past the previous occurrence
        if val in last_seen and last_seen[val] >= left:
            left = last_seen[val] + 1

        # Update the last seen index for this value
        last_seen[val] = right

        # Update the maximum window length
        current_len = right - left + 1
        if current_len > max_len:
            max_len = current_len

    return max_len
