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

    sorted_intervals = sorted(intervals, key=lambda x: x[1])

    last_point = float('-inf')
    count = 0

    for a, b in sorted_intervals:
        if a > last_point:
            last_point = b
            count += 1

    return count
