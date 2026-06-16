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

    # Sort by right endpoint (greedy: always stab at the earliest ending interval's right end)
    sorted_intervals = sorted(intervals, key=lambda iv: iv[1])

    count = 0
    last_point = None

    for (a, b) in sorted_intervals:
        # If last_point is None or strictly less than a, the current interval is not yet stabbed
        # Note: closed intervals, so if last_point == a, the point touches the left endpoint → already stabbed
        if last_point is None or last_point < a:
            count += 1
            last_point = b

    return count
