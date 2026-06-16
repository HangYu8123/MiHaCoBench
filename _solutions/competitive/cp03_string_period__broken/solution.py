"""Broken reference for competitive/cp03_string_period.

PLANTED DEFECT: Uses a naive O(n * m) substring scan instead of KMP.
This produces CORRECT answers on small inputs but TIMES OUT on the
adversarial complexity gate (text='a'*1_000_000, pattern='a'*499+'?').
"""
from __future__ import annotations


def count_pattern(text: str, pattern: str) -> list[int]:
    """Return all 0-indexed start positions where pattern occurs in text.

    BROKEN: naive O(n * m) scan — correct on small inputs, times out on large.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []

    results: list[int] = []
    for i in range(n - m + 1):
        # Check if text[i:i+m] matches pattern (with '?' wildcard)
        match = True
        for j in range(m):
            if pattern[j] != '?' and pattern[j] != text[i + j]:
                match = False
                break
        if match:
            results.append(i)
    return results
