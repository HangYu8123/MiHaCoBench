def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    result = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        last_start, last_end = result[-1]
        if start <= last_end:          # fix: <= handles touching intervals (c <= b)
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
