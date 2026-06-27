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

    # Fenwick tree (1-indexed), size n
    bit = [0] * (n + 1)

    def bit_update(i, delta):
        while i <= n:
            bit[i] += delta
            i += i & (-i)

    def bit_query(i):
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s

    # Sort queries by right endpoint, keeping original index
    sorted_qs = sorted(enumerate(queries), key=lambda x: x[1][1])

    ans = [0] * q
    last_seen = {}  # value -> last index where it appeared
    qi = 0  # pointer into sorted_qs

    for r in range(n):
        v = a[r]
        # Remove old contribution of v if it appeared before
        if v in last_seen:
            bit_update(last_seen[v] + 1, -1)
        # Add new contribution at position r (1-indexed: r+1)
        bit_update(r + 1, 1)
        last_seen[v] = r

        # Answer all queries with right endpoint == r
        while qi < q and sorted_qs[qi][1][1] == r:
            orig_idx, (l, _r) = sorted_qs[qi]
            # Range [l, r] in 0-indexed = prefix(r+1) - prefix(l) in 1-indexed BIT
            ans[orig_idx] = bit_query(r + 1) - bit_query(l)
            qi += 1

    return ans
