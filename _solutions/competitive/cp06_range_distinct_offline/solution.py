"""Gold reference for competitive/cp06_range_distinct_offline.

Offline "number of distinct values in a[l..r]" queries, answered in
O((n + q) log n) using a Fenwick / Binary Indexed Tree (BIT) and the classic
last-occurrence trick.

Idea
----
Process queries OFFLINE, grouped by their right endpoint ``r`` in increasing
order. Sweep ``i = 0, 1, ..., n - 1`` and maintain a Fenwick tree over the
``n`` positions whose values are 0/1:

  * Position ``p`` holds 1 iff ``p`` is the *latest* (right-most so far) index at
    which the value ``a[p]`` has been seen during the sweep up to the current
    ``i``.

When we advance the sweep to position ``i`` with value ``v``:

  * If ``v`` was previously seen at some position ``last[v] = p >= 0``, clear that
    older marker with ``bit.add(p, -1)`` (it is no longer the latest occurrence).
  * Set ``bit.add(i, +1)`` and record ``last[v] = i``.

At this point, for any query ``(l, r)`` with ``r == i`` the number of distinct
values in ``a[l..i]`` equals the number of positions ``p`` in ``[l, i]`` that
currently carry a 1 — because every distinct value contributes exactly one mark
(its latest occurrence at or before ``i``), and that mark lies inside ``[l, i]``
iff the value's latest occurrence is ``>= l`` (i.e. the value actually appears in
``a[l..i]``). That count is the prefix-sum range query ``bit.range_sum(l, i)``.

Answers are recorded against each query's original position so the returned list
matches the input order.

Total work: each position is added/removed O(1) times (each ``add`` is
O(log n)); each query is one range-sum (O(log n)). Overall O((n + q) log n).
"""
from __future__ import annotations


class _Fenwick:
    """1-indexed Fenwick / Binary Indexed Tree supporting point-add + prefix-sum."""

    __slots__ = ("n", "tree")

    def __init__(self, n: int) -> None:
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, i: int, delta: int) -> None:
        """Add ``delta`` at 0-indexed position ``i``."""
        i += 1  # to 1-indexed
        tree = self.tree
        while i <= self.n:
            tree[i] += delta
            i += i & (-i)

    def _prefix(self, i: int) -> int:
        """Sum of positions [0 .. i] (0-indexed, inclusive). i may be -1 -> 0."""
        i += 1  # to 1-indexed; i == 0 (0-indexed -1) -> loop body skipped
        tree = self.tree
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    def range_sum(self, l: int, r: int) -> int:
        """Sum of positions [l .. r], 0-indexed inclusive."""
        return self._prefix(r) - self._prefix(l - 1)


def range_distinct(a: list[int], queries: list[tuple]) -> list[int]:
    """Return, per query, the number of DISTINCT values in ``a[l..r]``.

    Parameters
    ----------
    a : list[int]
        The array of ``n`` values (any hashable ints).
    queries : list[tuple]
        List of ``(l, r)`` 0-indexed INCLUSIVE ranges with ``0 <= l <= r < n``.

    Returns
    -------
    list[int]
        One count per query, in the SAME order as ``queries``: the number of
        distinct values in the inclusive sub-array ``a[l..r]``.
    """
    n = len(a)
    q = len(queries)
    if q == 0:
        return []

    # Group query indices by right endpoint r so we can answer them during the
    # single left-to-right sweep when the sweep reaches position r.
    by_r: list[list[int]] = [[] for _ in range(n)]
    for qi, (l, r) in enumerate(queries):
        by_r[r].append(qi)

    bit = _Fenwick(n)
    last: dict = {}              # value -> most recent index seen during the sweep
    ans = [0] * q

    for i in range(n):
        v = a[i]
        prev = last.get(v, -1)
        if prev >= 0:
            bit.add(prev, -1)   # the old occurrence is no longer the latest
        bit.add(i, 1)
        last[v] = i
        # Answer every query whose right endpoint is exactly i.
        for qi in by_r[i]:
            l = queries[qi][0]
            ans[qi] = bit.range_sum(l, i)

    return ans
