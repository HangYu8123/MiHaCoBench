def min_stabbing_points(intervals: list[tuple]) -> int:
    """Return the minimum number of points on the real line such that every
    interval contains at least one chosen point.

    Each interval is a tuple ``(a, b)`` with ``a <= b`` and represents the
    **closed** interval ``[a, b]``. A point ``p`` **stabs** ``[a, b]`` iff
    ``a <= p <= b`` (inclusive at BOTH ends).

    An empty list returns ``0``.
    """
    if not intervals:
        return 0

    # Sort by right endpoint (greedy: always pick the rightmost possible point
    # that still stabs the current interval, which is b itself)
    sorted_intervals = sorted(intervals, key=lambda x: x[1])

    count = 0
    last_point = None  # the last stabbing point chosen

    for a, b in sorted_intervals:
        # If no point chosen yet, or the last point doesn't stab this interval
        if last_point is None or last_point < a:
            # Pick the right endpoint of this interval as the stabbing point
            last_point = b
            count += 1
        # else: last_point >= a and last_point <= b (since intervals sorted by b,
        # and last_point was set to some previous b <= current b), so it stabs this interval

    return count
