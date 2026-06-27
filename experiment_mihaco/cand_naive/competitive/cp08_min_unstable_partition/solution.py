"""
cp08_min_unstable_partition — fewest stable segments, lex-smallest cuts.

Approach:
1. Build sparse tables for range-min and range-max to answer O(1) RMQ queries
   after O(n log n) preprocessing.
2. Use binary search + RMQ to compute, for each index i, the farthest index
   reach[i] such that values[i..reach[i]] is stable (max - min <= K).
3. Run a greedy right-to-left pass to compute seg_from[i] = minimum number of
   segments needed to cover values[i..n-1].
4. Reconstruct the lex-smallest cut list by, at each step, choosing the earliest
   end index e >= current start such that:
   - values[start..e] is stable (max - min <= K), AND
   - seg_from[e+1] == remaining_segments - 1  (we can still finish with
     the required total).
   Binary search for this earliest e.
"""

import math


def _build_sparse_table(arr, func):
    """Build a sparse table for range queries using func (min or max)."""
    n = len(arr)
    if n == 0:
        return [], []
    LOG = max(1, int(math.log2(n)) + 1) if n > 0 else 1
    table = [arr[:]]
    for j in range(1, LOG + 1):
        prev = table[j - 1]
        length = 1 << j
        cur = []
        for i in range(n - length + 1):
            cur.append(func(prev[i], prev[i + (length >> 1)]))
        table.append(cur)
    return table


def _query(table, log2floor, l, r, func):
    """Query sparse table for [l, r] inclusive."""
    if l > r:
        raise ValueError("l > r")
    length = r - l + 1
    k = log2floor[length]
    return func(table[k][l], table[k][r - (1 << k) + 1])


def min_unstable_cuts(values: list[int], K: int) -> list[int]:
    n = len(values)
    if n == 1:
        return [0]

    # Precompute floor(log2(i)) for i in 1..n
    log2floor = [0] * (n + 1)
    for i in range(2, n + 1):
        log2floor[i] = log2floor[i >> 1] + 1

    # Build sparse tables for range min and max
    min_table = _build_sparse_table(values, min)
    max_table = _build_sparse_table(values, max)

    def range_stable(l, r):
        """Return True if values[l..r] is stable (max - min <= K)."""
        rmax = _query(max_table, log2floor, l, r, max)
        rmin = _query(min_table, log2floor, l, r, min)
        return rmax - rmin <= K

    # For each start index i, compute reach[i] = farthest index reachable in
    # one stable segment starting at i.
    # Use binary search: the stability property is monotone (if [i..r] is
    # stable then so is [i..r-1]).
    reach = [0] * n
    for i in range(n):
        lo, hi = i, n - 1
        while lo < hi:
            mid = (lo + hi + 1) >> 1
            if range_stable(i, mid):
                lo = mid
            else:
                hi = mid - 1
        reach[i] = lo

    # seg_from[i] = minimum number of segments to cover values[i..n-1]
    # seg_from[n] = 0 (empty suffix needs 0 segments)
    seg_from = [0] * (n + 1)
    seg_from[n] = 0
    # Fill right-to-left
    for i in range(n - 1, -1, -1):
        # We must start a new segment at i; it can extend to reach[i]
        # Best strategy: take as far as possible to minimize segment count
        # seg_from[i] = 1 + min(seg_from[j+1]) for j in [i, reach[i]]
        # Since seg_from is non-increasing as j increases (farther reach = fewer
        # remaining segments), the minimum is achieved at j = reach[i].
        seg_from[i] = 1 + seg_from[reach[i] + 1]

    # Total minimum segments
    m = seg_from[0]

    # Reconstruct lex-smallest cut list.
    # At each step with current start `s` and `remaining` segments left to place:
    # We need to find the SMALLEST e >= s such that:
    #   (a) values[s..e] is stable, i.e., e <= reach[s]
    #   (b) seg_from[e+1] == remaining - 1
    #
    # Since seg_from is non-increasing (weakly), we binary search for the
    # smallest e in [s, reach[s]] where seg_from[e+1] == remaining - 1.
    # Note: seg_from[reach[s]+1] = seg_from[0] based values — actually we need
    # seg_from[e+1] = remaining - 1.
    # The condition seg_from[e+1] >= remaining - 1 is equivalent to "we haven't
    # yet gone far enough", and seg_from[e+1] <= remaining - 1 means "we've
    # covered enough".
    # Binary search: find smallest e where seg_from[e+1] <= remaining - 1.

    result = []
    s = 0
    remaining = m

    while s < n:
        if remaining == 1:
            # Must take all the rest
            result.append(n - 1)
            break
        # Find smallest e in [s, reach[s]] such that seg_from[e+1] == remaining - 1
        # seg_from is non-increasing as e increases (larger e => smaller suffix)
        # We want seg_from[e+1] <= remaining - 1; find smallest such e.
        lo, hi = s, reach[s]
        # At e = reach[s]: seg_from[reach[s]+1] = seg_from[0 for next start]
        # We need seg_from[e+1] == remaining - 1 for the earliest e.
        # Binary search for smallest e where seg_from[e+1] <= remaining - 1
        ans_e = reach[s]  # fallback (should always work if m is correct)
        lo2, hi2 = s, reach[s]
        while lo2 <= hi2:
            mid = (lo2 + hi2) >> 1
            if seg_from[mid + 1] <= remaining - 1:
                ans_e = mid
                hi2 = mid - 1
            else:
                lo2 = mid + 1

        result.append(ans_e)
        s = ans_e + 1
        remaining -= 1

    return result
