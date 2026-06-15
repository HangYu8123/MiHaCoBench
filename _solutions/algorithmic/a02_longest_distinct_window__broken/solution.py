"""Deliberately-broken reference for algorithmic/a02_longest_distinct_window.

Planted defect: O(n^2) brute-force implementation that recomputes the
distinct-elements set from scratch for every starting index. This passes
all small correctness tests but fails the large-input timing gate (N=1_000_000
within 5.0 seconds) because it runs in O(n^2) time.

This MUST fail the grader (proves the grader discriminates).
"""
from __future__ import annotations


def longest_distinct_window(seq: list[int]) -> int:
    """O(n^2) brute-force: try every starting index and extend while distinct.

    Correct output on small inputs; too slow for the large-input gate.
    """
    if not seq:
        return 0

    n = len(seq)
    best = 0
    for left in range(n):
        seen = set()
        for right in range(left, n):
            val = seq[right]
            if val in seen:
                break
            seen.add(val)
            window_len = right - left + 1
            if window_len > best:
                best = window_len
    return best
