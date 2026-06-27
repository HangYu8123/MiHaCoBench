def longest_distinct_window(seq: list[int]) -> int:
    last_seen: dict[int, int] = {}
    left = 0
    max_len = 0
    for right, val in enumerate(seq):
        if val in last_seen and last_seen[val] >= left:
            left = last_seen[val] + 1
        last_seen[val] = right
        max_len = max(max_len, right - left + 1)
    return max_len
