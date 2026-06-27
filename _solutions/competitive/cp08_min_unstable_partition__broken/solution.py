"""Broken reference for competitive/cp08_min_unstable_partition.

PLANTED DEFECT (subtle, plausible): plain greedy — extend each segment as FAR as
possible (cut at ``reach[pos]``). This produces a partition with the correct
MINIMUM number of segments, so it looks right and passes any test that only
checks the count or validity. But "extend as far as possible" yields the
lexicographically *largest* end indices, whereas the contract demands the
lexicographically *smallest*. On any input where an earlier cut is possible
without increasing the segment count, this returns the wrong list.

The reach computation is identical to the gold; only the final cut-selection
differs.
"""
from __future__ import annotations

from collections import deque


def min_unstable_cuts(values: list[int], K: int) -> list[int]:
    """BROKEN: greedy-farthest cuts (right count, but lex-LARGEST ends)."""
    n = len(values)
    if n == 0:
        return []

    reach = [0] * n
    maxd: deque[int] = deque()
    mind: deque[int] = deque()
    r = 0
    for i in range(n):
        if r < i:
            r = i
            maxd.clear()
            mind.clear()
        while r < n:
            x = values[r]
            cur_max = x if not maxd else (values[maxd[0]] if values[maxd[0]] > x else x)
            cur_min = x if not mind else (values[mind[0]] if values[mind[0]] < x else x)
            if cur_max - cur_min <= K:
                while maxd and values[maxd[-1]] <= x:
                    maxd.pop()
                maxd.append(r)
                while mind and values[mind[-1]] >= x:
                    mind.pop()
                mind.append(r)
                r += 1
            else:
                break
        reach[i] = r - 1
        if maxd and maxd[0] == i:
            maxd.popleft()
        if mind and mind[0] == i:
            mind.popleft()

    # BUG: cut as far as possible each time -> minimum count but lex-LARGEST ends.
    res: list[int] = []
    pos = 0
    while pos < n:
        e = reach[pos]
        res.append(e)
        pos = e + 1
    return res
