"""Broken reference for algorithmic/a10_kth_distinct_in_window.

PLANTED DEFECT (the inclusive-boundary ambiguity): the "enough distinct values"
threshold is written as ``distinct > k`` instead of ``distinct >= k``. So when a
window has EXACTLY ``k`` distinct values — the boundary case — it wrongly reports
``None`` instead of the k-th (here, the largest) distinct value. Windows with more
than ``k`` distinct values and windows with fewer than ``k`` both behave correctly,
so only the exact-``k`` boundary reveals the bug. The algorithm is otherwise the
efficient BIT-based gold, so it still passes the time gate.
"""
from __future__ import annotations


class _BIT:
    def __init__(self, m: int) -> None:
        self.m = m
        self.t = [0] * (m + 1)
        self._hi = 1 << (m.bit_length() - 1) if m >= 1 else 0

    def update(self, i: int, delta: int) -> None:
        while i <= self.m:
            self.t[i] += delta
            i += i & (-i)

    def kth(self, k: int) -> int:
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
    """BROKEN: uses ``distinct > k`` (exclusive) instead of ``distinct >= k``."""
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
        if distinct > k:                        # BUG: should be >= k (exact-k -> None)
            out.append(uniq[bit.kth(k) - 1])
        else:
            out.append(None)
        if i < last:
            remove(a[i])
            add(a[i + w])
    return out
