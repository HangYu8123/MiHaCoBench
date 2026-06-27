"""Gold reference for algorithmic/a10_kth_distinct_in_window.

For each contiguous window of width ``w`` over ``a``, report the k-th SMALLEST
DISTINCT value present in that window (1-indexed), or ``None`` when the window has
fewer than ``k`` distinct values.

Efficient approach (O((n) log V)): slide the window maintaining a value->count
map and a Fenwick/BIT over the compressed value domain, where a value contributes
1 to the BIT exactly while its count is >= 1. The k-th distinct value is then a
single binary-lifted prefix walk on the BIT. A naive per-window rebuild of the
distinct set is O(n * w) and times out on the large gate.
"""
from __future__ import annotations


class _BIT:
    """Fenwick tree supporting point update and 'smallest index with prefix>=k'."""

    def __init__(self, m: int) -> None:
        self.m = m
        self.t = [0] * (m + 1)
        self._hi = 1 << (m.bit_length() - 1) if m >= 1 else 0

    def update(self, i: int, delta: int) -> None:
        while i <= self.m:
            self.t[i] += delta
            i += i & (-i)

    def kth(self, k: int) -> int:
        """Return the 1-indexed position of the k-th present element (assumes k<=total)."""
        idx = 0
        rem = k
        pw = self._hi
        while pw > 0:
            nxt = idx + pw
            if nxt <= self.m and self.t[nxt] < rem:
                idx = nxt
                rem -= self.t[nxt]
            pw >>= 1
        return idx + 1


def kth_distinct_in_window(a: list[int], w: int, k: int) -> list:
    """Return one answer per width-``w`` window: the k-th smallest distinct value
    (1-indexed) or ``None`` if the window has fewer than ``k`` distinct values.

    Raises ``ValueError`` if ``w < 1`` or ``k < 1``. Returns ``[]`` when ``w > len(a)``
    (no full window fits). The output has length ``len(a) - w + 1`` otherwise.
    """
    if w < 1 or k < 1:
        raise ValueError("w and k must be >= 1")
    n = len(a)
    if w > n:
        return []

    uniq = sorted(set(a))
    rank = {v: i + 1 for i, v in enumerate(uniq)}
    m = len(uniq)
    bit = _BIT(m)
    counts = [0] * (m + 1)
    distinct = 0

    def add(x: int) -> None:
        nonlocal distinct
        r = rank[x]
        counts[r] += 1
        if counts[r] == 1:
            bit.update(r, 1)
            distinct += 1

    def remove(x: int) -> None:
        nonlocal distinct
        r = rank[x]
        counts[r] -= 1
        if counts[r] == 0:
            bit.update(r, -1)
            distinct -= 1

    for x in a[:w]:
        add(x)

    out: list = []
    last = n - w
    for i in range(last + 1):
        if distinct >= k:                       # inclusive: exactly-k distinct still yields a value
            out.append(uniq[bit.kth(k) - 1])
        else:
            out.append(None)
        if i < last:
            remove(a[i])
            add(a[i + w])
    return out
