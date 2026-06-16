"""Gold reference for algorithmic/a09_interval_stab.

Greedy: sort intervals by right endpoint; place a point at the right endpoint of
the first not-yet-stabbed interval. Because intervals are CLOSED, an interval is
already stabbed by the last placed point ``p`` iff its left endpoint ``a <= p``
(inclusive), so touching intervals share a point.
"""
from __future__ import annotations


def min_stabbing_points(intervals: list[tuple]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals, key=lambda iv: iv[1])
    points = 0
    last_point = None
    for a, b in ordered:
        # Closed intervals: a <= last_point means this interval is already stabbed.
        if last_point is None or a > last_point:
            points += 1
            last_point = b
    return points
