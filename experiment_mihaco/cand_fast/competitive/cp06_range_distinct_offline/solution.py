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
    if not queries:
        return []

    n = len(a)

    # Fenwick tree (BIT) with 1-based internal indexing.
    # Caller passes 0-based positions; internally stored at i+1.
    bit = [0] * (n + 1)

    def bit_update(i, delta):
        # Convert 0-based position i to 1-based index.
        i += 1
        while i <= n:
            bit[i] += delta
            i += i & (-i)

    def bit_query(i):
        # Prefix sum over [0..i] (0-based), i.e. [1..i+1] internally.
        # For i < 0, returns 0 (never called with i < 0 due to guard below).
        i += 1
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s

    # Sort queries by right endpoint, preserving original indices.
    sorted_queries = sorted(enumerate(queries), key=lambda x: x[1][1])

    answers = [0] * len(queries)
    last_seen = {}  # value -> last index where it appeared (0-based)
    q_ptr = 0
    q_count = len(sorted_queries)

    for r in range(n):
        v = a[r]
        # Remove old contribution of this value if it was seen before.
        if v in last_seen:
            bit_update(last_seen[v], -1)
        # Add new contribution at current position.
        bit_update(r, 1)
        last_seen[v] = r

        # Answer all queries whose right endpoint is r.
        while q_ptr < q_count and sorted_queries[q_ptr][1][1] == r:
            orig_idx, (l, _r) = sorted_queries[q_ptr]
            if l == 0:
                answers[orig_idx] = bit_query(r)
            else:
                answers[orig_idx] = bit_query(r) - bit_query(l - 1)
            q_ptr += 1

    return answers
