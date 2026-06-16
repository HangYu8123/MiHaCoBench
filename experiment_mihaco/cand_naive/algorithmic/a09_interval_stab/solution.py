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

    # Sort by right endpoint (greedy: pick rightmost point of earliest-ending interval)
    sorted_intervals = sorted(intervals, key=lambda iv: iv[1])

    count = 0
    # Use a sentinel that is guaranteed to not stab any interval initially
    last_point = None

    for a, b in sorted_intervals:
        # If no point yet, or the last chosen point doesn't stab this interval
        if last_point is None or last_point < a:
            # Place a new point at the right endpoint (stabs as many future intervals as possible)
            last_point = b
            count += 1
        # else: last_point is in [a, b] because last_point >= a and last_point <= b
        # (since we sorted by b and last_point was set to some previous b' <= b,
        #  and we only enter else when last_point >= a, so a <= last_point <= b)

    return count
