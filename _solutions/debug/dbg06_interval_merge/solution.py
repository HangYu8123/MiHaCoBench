"""Gold reference for debug/dbg06_interval_merge — interval merger (stdlib only).

Two bugs were present in the original code:
(a) Touching intervals (sharing an endpoint) were not merged because the
    merge condition used strict inequality (start < last_end) instead of
    (start <= last_end).
(b) The input was not sorted before merging, so unsorted intervals produced
    wrong results.

The fix sorts by start endpoint first, then merges with the correct
non-strict condition.
"""
from __future__ import annotations


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge all overlapping and touching intervals.

    Sorts by start endpoint, then performs a single linear scan, merging
    whenever two intervals overlap or share an endpoint (c <= b).

    Returns a list of non-overlapping, non-touching intervals sorted by
    start endpoint.
    """
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda iv: (iv[0], iv[1]))
    result = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        last_start, last_end = result[-1]
        if start <= last_end:          # <= handles both overlap and touching
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
