"""Deliberately-broken reference for competitive/cp06_range_distinct_offline.

Planted defect: the naive per-query implementation that materialises a slice and
counts distinct values with ``len(set(a[l:r+1]))`` for every query independently.

This is CORRECT for all small test cases (it produces identical answers to the
gold), but it is O(n) per query and therefore O(n * q) overall. On the hard
complexity gate (n ~ 1e5, q ~ 1e5) that is on the order of 1e10 operations and
TIMES OUT, while the O((n + q) log n) Fenwick gold finishes comfortably.

The defect is LOCALIZED to complexity: every correctness test (small n) PASSES;
only the adversarial time-gate test FAILS.
"""
from __future__ import annotations


def range_distinct(a: list[int], queries: list[tuple]) -> list[int]:
    """Return, per query, the number of DISTINCT values in ``a[l..r]``.

    BUG: O(n) per query (builds ``set(a[l:r+1])`` each time) -> O(n * q) total.
    Correct on small inputs but times out on the large adversarial gate.
    """
    out: list[int] = []
    for l, r in queries:
        out.append(len(set(a[l:r + 1])))
    return out
