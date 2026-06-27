def longest_distinct_window(seq: list[int]) -> int:
    """Return the length of the longest contiguous subarray with all distinct elements.

    Uses an O(n) sliding-window approach with a last-seen dict.
    The left pointer only moves forward; a max() guard prevents stale
    last_seen entries from moving left backward.
    """
    last_seen: dict[int, int] = {}
    left = 0
    max_len = 0

    for right, val in enumerate(seq):
        if val in last_seen:
            # Jump left past the previous occurrence, but never move backward.
            left = max(left, last_seen[val] + 1)
        last_seen[val] = right
        window_len = right - left + 1
        if window_len > max_len:
            max_len = window_len

    return max_len


if __name__ == "__main__":
    # Correctness assertions against all six spec examples.
    assert longest_distinct_window([]) == 0, "empty list must return 0"
    assert longest_distinct_window([5]) == 1, "single element must return 1"
    assert longest_distinct_window([1, 2, 3, 4]) == 4, "all distinct"
    assert longest_distinct_window([1, 1, 1, 1]) == 1, "all identical"
    assert longest_distinct_window([1, 2, 3, 1, 2, 3, 4, 5]) == 5, "mixed example 1"
    assert longest_distinct_window([1, 2, 1, 3, 2, 4]) == 4, "mixed example 2"
    print("All correctness assertions passed.")

    # Complexity smoke test — must complete well within 5.0 s.
    import time

    n = 1_000_000

    # All-distinct case: expected result = n.
    data_distinct = list(range(n))
    t0 = time.perf_counter()
    result = longest_distinct_window(data_distinct)
    elapsed = time.perf_counter() - t0
    assert result == n, f"all-distinct expected {n}, got {result}"
    print(f"all-distinct n={n}: result={result}, elapsed={elapsed:.3f}s")

    # All-same case: expected result = 1.
    data_same = [0] * n
    t0 = time.perf_counter()
    result = longest_distinct_window(data_same)
    elapsed = time.perf_counter() - t0
    assert result == 1, f"all-same expected 1, got {result}"
    print(f"all-same    n={n}: result={result}, elapsed={elapsed:.3f}s")

    print("All smoke tests passed.")
