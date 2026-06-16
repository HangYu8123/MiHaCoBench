"""
Offline distinct-count range queries using BIT (Fenwick tree) + last-occurrence trick.
Time complexity: O((n + q) log n)
Space complexity: O(n + q)
"""
from collections import defaultdict


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
    q = len(queries)

    # BIT (1-indexed), size n+1
    bit = [0] * (n + 1)

    def update(i: int, delta: int) -> None:
        # i is 0-indexed; convert to 1-indexed
        i += 1
        while i <= n:
            bit[i] += delta
            i += i & (-i)

    def prefix_sum(i: int) -> int:
        # i is 0-indexed; convert to 1-indexed
        i += 1
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s

    def range_sum(l: int, r: int) -> int:
        # Both l and r are 0-indexed inclusive
        if l == 0:
            return prefix_sum(r)
        return prefix_sum(r) - prefix_sum(l - 1)

    # Group queries by right endpoint (r), storing (l, original_index)
    q_at = defaultdict(list)
    for idx, (l, r) in enumerate(queries):
        q_at[r].append((l, idx))

    # Answer array in original query order
    ans = [0] * q

    # last_seen[v] = last index where value v was seen (0-indexed), or -1 if not seen
    last_seen = {}

    # Sweep right endpoint from 0 to n-1
    for i in range(n):
        v = a[i]
        prev = last_seen.get(v, -1)
        if prev >= 0:
            # Remove old contribution at prev position
            update(prev, -1)
        # Place new contribution at current position i
        update(i, 1)
        last_seen[v] = i

        # Answer all queries with right endpoint == i
        if i in q_at:
            for (l, idx) in q_at[i]:
                ans[idx] = range_sum(l, i)

    return ans
