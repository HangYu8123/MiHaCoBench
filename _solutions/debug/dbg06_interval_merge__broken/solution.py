"""Deliberately-broken reference for debug/dbg06_interval_merge.

Planted defects (mirrors the buggy code shown in TASK.md):
(a) The merge condition is strict (start < last_end) so touching intervals
    that share an endpoint are NOT merged — they are left as separate intervals.
(b) The input is NOT sorted before merging, so unsorted input produces
    incorrect results (later intervals that start before earlier ones are
    never merged with them).

Success cases (clearly-overlapping sorted intervals, empty list, single
interval, fully-nested interval) still work correctly, so the defect is
localized — the grader must catch the missing touching-merge and the
missing sort.
"""
from __future__ import annotations


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    result = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = result[-1]
        if start < last_end:          # BUG: should be <= to handle touching intervals
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
