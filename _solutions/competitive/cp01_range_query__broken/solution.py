"""Deliberately-broken reference for competitive/cp01_range_query.

Planted defect: naive O(n) per-operation implementation.

The range_add iterates over every element in [l, r] and the range_sum
iterates over every element as well — so each operation costs O(n) in the
worst case. For n = 200 000 and q = 200 000, this is O(N * Q) ≈ 4 × 10^10
operations, which takes many minutes and therefore TIMES OUT on the hard gate
test that requires completion within 5 seconds.

Correctness on small inputs is PERFECT (same values as the gold), so all the
small correctness tests pass. Only the hard time-gate fails, making the
defect localized.
"""
from __future__ import annotations


def process_queries(n: int, ops: list[tuple]) -> list[int]:
    """Process range-add and range-sum queries on an array of n zeros.

    BUG: naive O(n) per-operation — correct but too slow for large n/q.
    Times out on the hard complexity gate (n=200000, q=200000, timeout=5s).
    """
    arr = [0] * n

    results: list[int] = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            # O(n) per add — the planted defect
            for i in range(l, r + 1):
                arr[i] += v
        else:
            _, l, r = op
            # O(n) per sum — the planted defect
            results.append(sum(arr[l:r + 1]))
    return results
