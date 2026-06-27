"""
Range distinct count queries — offline O((n + q) log n) approach.

Algorithm:
- Sort queries by right endpoint r.
- Sweep r from 0 to n-1:
    * For each position i reaching r, track prev[a[r]] = last occurrence of a[r].
    * Add +1 at position r, remove -1 at prev[a[r]] (if exists).
    * For queries with right endpoint == r, query prefix sum [l..r] in the BIT.

The key insight: for a value v appearing at positions p1 < p2 < ... < pk <= r,
only pk contributes to [l..r] if l <= pk. The BIT stores 1 at the most recent
occurrence of each distinct value seen so far, so a prefix sum from l to r
gives exactly the count of distinct values in a[l..r].
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

    # Fenwick Tree (BIT) — 1-indexed internally, size n
    bit = [0] * (n + 1)

    def bit_update(i, delta):
        # i is 0-indexed; convert to 1-indexed
        i += 1
        while i <= n:
            bit[i] += delta
            i += i & (-i)

    def bit_query(i):
        # prefix sum [0..i] (0-indexed i)
        i += 1  # convert to 1-indexed
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s

    def bit_range(l, r):
        # sum of [l..r] inclusive, 0-indexed
        if l == 0:
            return bit_query(r)
        return bit_query(r) - bit_query(l - 1)

    # Group queries by right endpoint
    # queries_by_r[r] = list of (original_index, l)
    queries_by_r = [[] for _ in range(n)]
    for idx, (l, r) in enumerate(queries):
        queries_by_r[r].append((idx, l))

    results = [0] * q
    last_occ = {}  # value -> last seen position (0-indexed)

    for r in range(n):
        v = a[r]
        if v in last_occ:
            # Remove previous occurrence from BIT
            bit_update(last_occ[v], -1)
        # Add current position to BIT
        bit_update(r, 1)
        last_occ[v] = r

        # Answer all queries with right endpoint == r
        for idx, l in queries_by_r[r]:
            results[idx] = bit_range(l, r)

    return results
