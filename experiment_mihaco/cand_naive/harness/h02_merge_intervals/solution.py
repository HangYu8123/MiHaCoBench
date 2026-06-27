from copy import deepcopy


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Coalesce half-open intervals into the minimal list of disjoint intervals."""
    # Validate first (before any other processing), without mutating input.
    for iv in intervals:
        start, end = iv[0], iv[1]
        if start > end:
            raise ValueError(f"invalid interval: start {start} > end {end}")

    # Build a private, non-mutating list of non-empty intervals.
    work = [deepcopy((iv[0], iv[1])) for iv in intervals if iv[0] != iv[1]]

    if not work:
        return []

    # Sort by start ascending (then end), purely on our own copies.
    work.sort(key=lambda iv: (iv[0], iv[1]))

    merged: list[tuple[int, int]] = []
    cur_start, cur_end = work[0]

    for start, end in work[1:]:
        if start <= cur_end:
            # Overlapping or exactly adjacent (half-open): coalesce.
            if end > cur_end:
                cur_end = end
        else:
            # Gap: emit the running interval and start a new one.
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end

    merged.append((cur_start, cur_end))
    return merged
