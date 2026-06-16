"""Deliberately-broken reference for algorithmic/a09_interval_stab.

Planted defect: the "already stabbed" test uses a STRICT boundary (``a >= last_point``
to start a new point), i.e. it treats the intervals as half-open. When an interval
merely TOUCHES the last placed point (``a == last_point``) it is wrongly counted as
unstabbed, so touching intervals each get their own point. Non-touching inputs are
unaffected.
"""
from __future__ import annotations


def min_stabbing_points(intervals: list[tuple]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals, key=lambda iv: iv[1])
    points = 0
    last_point = None
    for a, b in ordered:
        # BUG: `a >= last_point` treats a touching endpoint as not stabbed.
        if last_point is None or a >= last_point:
            points += 1
            last_point = b
    return points
