"""Deliberately-broken reference for competitive/cp05_kth_subarray_sum.

Planted defect: naive O(n^2) brute force — enumerate every contiguous-subarray
sum, sort, and index the k-th smallest.

This is CORRECT for all small test cases (it produces identical answers to the
gold reference), but TIMES OUT on the hard complexity gate (n = 120000,
timeout = 8s) because enumerating n*(n+1)/2 = ~7.2e9 subarray sums is far beyond
what fits in the time (and memory) budget; an O(n log(totalSum)) approach is
required.

The defect is LOCALIZED to algorithmic complexity: every correctness test (small
n) PASSES; only the adversarial time-gate test FAILS. The module imports and runs
cleanly.
"""
from __future__ import annotations


def kth_subarray_sum(a: list[int], k: int) -> int:
    """Return the k-th smallest contiguous-subarray sum (1-indexed) of ``a``.

    BUG: enumerates ALL n*(n+1)/2 subarray sums and sorts them — O(n^2 log n) time
    and O(n^2) memory. Correct on small inputs, but times out on the large gate.
    """
    n = len(a)
    if n == 1:
        return a[0]

    sums: list[int] = []
    for i in range(n):
        running = 0
        for j in range(i, n):
            running += a[j]
            sums.append(running)
    sums.sort()
    return sums[k - 1]
