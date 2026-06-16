"""
Offline range-distinct-count queries using the last-occurrence + Fenwick BIT trick.

Algorithm (O((n + q) log n)):
1. Sort queries by right endpoint r.
2. Sweep r from 0..n-1:
   - For each new element a[r], if it appeared before at position prev,
     subtract 1 from BIT at prev (un-count it), then add 1 at r.
   - Answer all queries with right endpoint == r by querying prefix sum [l..r].
3. Restore answer order.

A prefix-sum query BIT.query(r) - BIT.query(l-1) gives the count of distinct
values in a[l..r], because exactly one occurrence of each distinct value
(the rightmost one seen so far) has a +1 in the BIT.
"""


def range_distinct(a: list[int], queries: list[tuple]) -> list[int]:
    """Answer offline range-distinct-count queries.

    Parameters
    ----------
    a : list[int]
        The array of values (any hashable ints), length n >= 1.
    queries : list[tuple]
        A list of ``(l, r)`` pairs, each a **0-indexed INCLUSIVE** range with
        ``0 <= l <= r < n``.

    Returns
    -------
    list[int]
        One integer per query, in the **same order as the input queries**: the
        number of DISTINCT values in ``a[l..r]`` (inclusive).
    """
    n = len(a)
    q = len(queries)

    if q == 0:
        return []

    # Fenwick Tree (1-indexed, size n)
    bit = [0] * (n + 1)

    def update(i, delta):
        # i is 0-indexed; convert to 1-indexed
        i += 1
        while i <= n:
            bit[i] += delta
            i += i & (-i)

    def prefix_query(i):
        # sum [0..i] (0-indexed), i.e., [1..i+1] in 1-indexed
        i += 1
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s

    def range_query(l, r):
        if l == 0:
            return prefix_query(r)
        return prefix_query(r) - prefix_query(l - 1)

    # Sort queries by right endpoint, preserving original index
    sorted_queries = sorted(range(q), key=lambda idx: queries[idx][1])

    answers = [0] * q
    last_seen = {}  # value -> last index where it appeared
    qi = 0  # pointer into sorted_queries

    for r in range(n):
        val = a[r]
        if val in last_seen:
            # Remove the previous occurrence from BIT
            update(last_seen[val], -1)
        # Add current occurrence
        update(r, 1)
        last_seen[val] = r

        # Answer all queries with right endpoint == r
        while qi < q and queries[sorted_queries[qi]][1] == r:
            orig_idx = sorted_queries[qi]
            l, _ = queries[orig_idx]
            answers[orig_idx] = range_query(l, r)
            qi += 1

    return answers
