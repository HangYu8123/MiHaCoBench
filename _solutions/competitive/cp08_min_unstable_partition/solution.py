"""Gold reference for competitive/cp08_min_unstable_partition.

Partition ``values`` into the FEWEST contiguous segments with ``max-min <= K`` per
segment, and among all such minimum partitions return the one whose list of
segment END indices (0-based, inclusive) is LEXICOGRAPHICALLY SMALLEST.

Two coupled observations
------------------------
1. ``reach[i]`` = the farthest index ``j`` such that ``values[i..j]`` has
   ``max-min <= K``. Because the window max/min are monotone as the right end
   grows and ``reach`` is non-decreasing in ``i``, all ``reach[i]`` can be found
   in O(n) with a single two-pointer sweep backed by two monotonic deques (one
   for the running max, one for the running min).

2. ``minseg[i]`` = minimum segments needed to cover ``values[i..n-1]`` =
   ``1 + minseg[reach[i] + 1]`` (with ``minseg[n] = 0``), filled right-to-left.
   The global minimum is ``m = minseg[0]``.

Lexicographically-smallest END indices means: cut as EARLY as possible at every
step while still being able to finish the suffix within the remaining segment
budget. Greedy-farthest cutting gives the right COUNT but the lexicographically
LARGEST ends — the opposite of what is asked. Since ``minseg`` is non-increasing
in its index, for a remaining budget ``rem`` the earliest legal cut ``e`` is the
leftmost index in ``[pos, reach[pos]]`` with ``minseg[e+1] <= rem-1`` (binary
search). Sub-segments of a valid segment are themselves valid (``max-min`` only
shrinks), so whenever the suffix needs fewer than ``rem`` segments we can always
realise exactly ``rem`` by splitting — which the lex rule does by emitting early
single-element cuts.

Complexity: O(n) for reach + minseg, O(m log n) for the cut search → O(n log n).
"""
from __future__ import annotations

from collections import deque


def min_unstable_cuts(values: list[int], K: int) -> list[int]:
    """Return the lex-smallest list of segment end indices of a minimum partition.

    Parameters
    ----------
    values : list[int]
        The sequence to partition (length n >= 1).
    K : int
        Non-negative stability threshold: each segment must have ``max-min <= K``.

    Returns
    -------
    list[int]
        Ascending list of segment end indices (0-based, inclusive); the last
        element is always ``n-1``. Empty list when ``values`` is empty.
    """
    n = len(values)
    if n == 0:
        return []

    # 1. reach[i] via two-pointer + monotonic deques (deques hold indices of the
    #    current window [i .. r-1]; fronts are the window max / min).
    reach = [0] * n
    maxd: deque[int] = deque()
    mind: deque[int] = deque()
    r = 0
    for i in range(n):
        if r < i:  # safety; in practice r >= i always (single elements are valid)
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

    # 2. minseg[i] = 1 + minseg[reach[i] + 1], right-to-left.
    minseg = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        minseg[i] = 1 + minseg[reach[i] + 1]
    m = minseg[0]

    # 3. Earliest legal cut at each step (lex-smallest ends).
    res: list[int] = []
    pos = 0
    rem = m
    while pos < n:
        target = rem - 1
        lo, hi = pos, reach[pos]
        # minseg[e+1] is non-increasing in e -> leftmost e with minseg[e+1] <= target.
        while lo < hi:
            mid = (lo + hi) // 2
            if minseg[mid + 1] <= target:
                hi = mid
            else:
                lo = mid + 1
        res.append(lo)
        pos = lo + 1
        rem -= 1

    return res
