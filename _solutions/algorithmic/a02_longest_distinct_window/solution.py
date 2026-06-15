"""Gold reference for algorithmic/a02_longest_distinct_window.

Public contract
---------------
longest_distinct_window(seq: list[int]) -> int

Return the length of the longest contiguous subarray whose elements are all
distinct (no duplicates within the window). Returns 0 for an empty list.

Implementation
--------------
Classic O(n) sliding window with a hash map:
  - Maintain a window [left, right).
  - For each new right element, if it was last seen at index k >= left,
    advance left to k + 1 (shrink the window past the duplicate).
  - Record the maximum window length seen.
This is O(n) time and O(n) space (dict stores at most n entries).
"""
from __future__ import annotations


def longest_distinct_window(seq: list[int]) -> int:
    """Return the length of the longest contiguous subarray with all-distinct elements.

    Uses a sliding-window + last-seen dict for O(n) time complexity.
    Returns 0 for an empty list, 1 for a single element.
    """
    if not seq:
        return 0

    last_seen: dict[int, int] = {}  # value -> index of most recent occurrence
    left = 0
    best = 0

    for right, val in enumerate(seq):
        # If val was already in the window, advance left past the old occurrence.
        if val in last_seen and last_seen[val] >= left:
            left = last_seen[val] + 1
        last_seen[val] = right
        window_len = right - left + 1
        if window_len > best:
            best = window_len

    return best
