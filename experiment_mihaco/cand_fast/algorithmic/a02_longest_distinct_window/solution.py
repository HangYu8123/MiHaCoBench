def longest_distinct_window(seq: list[int]) -> int:
    left = 0
    best = 0
    last_seen: dict[int, int] = {}

    for right, val in enumerate(seq):
        if val in last_seen and last_seen[val] >= left:
            left = last_seen[val] + 1
        last_seen[val] = right
        window_len = right - left + 1
        if window_len > best:
            best = window_len

    return best
