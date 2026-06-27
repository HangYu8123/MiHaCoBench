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

    # Sort by right endpoint ascending; ties broken arbitrarily (stable sort)
    sorted_intervals = sorted(intervals, key=lambda x: x[1])

    # Place the first stabbing point at the right end of the first interval
    count = 1
    point = sorted_intervals[0][1]

    for a, b in sorted_intervals[1:]:
        # Strict greater-than: closed intervals share touching endpoints,
        # so a == point means the current point already stabs this interval.
        if a > point:
            count += 1
            point = b

    return count
