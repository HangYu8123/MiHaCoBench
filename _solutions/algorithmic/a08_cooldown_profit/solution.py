"""Gold reference for algorithmic/a08_cooldown_profit.

Maximum-profit selection of non-overlapping weighted intervals with a mandatory
cooldown gap between consecutive chosen jobs.

Algorithm (O(n log n)):
  * Sort jobs by END ascending.
  * dp[i] = best achievable profit considering the first i jobs (in end order).
    dp is non-decreasing in i, so the prefix maximum is dp itself.
  * For job i = (s, e, p), a previously chosen job must end no later than
    s - gap (cooldown). Binary-search the sorted ends for the count k of jobs
    whose end <= s - gap; those are exactly the jobs that may precede job i.
        dp[i+1] = max(dp[i], p + dp[k])
  * Answer is dp[n].

A naive O(n^2) DP is correct but blows the feasibility gate; a greedy that picks
highest-profit-first is asymptotically fast but WRONG (suboptimal).
"""
from __future__ import annotations

import bisect


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Return the maximum total profit of a cooldown-respecting job selection.

    Each job is a tuple ``(start, end, profit)`` with integer ``start < end`` and
    ``profit >= 0``. Jobs are half-open intervals ``[start, end)``. A subset is
    valid when, ordering the chosen jobs by position, every job's ``start`` is at
    least the previous chosen job's ``end`` plus ``gap`` (a mandatory cooldown of
    at least ``gap`` between consecutive selected jobs). Two jobs with
    ``prevEnd + gap <= nextStart`` may both be chosen.

    Returns the maximum total profit, or 0 if ``jobs`` is empty.
    """
    if not jobs:
        return 0

    # Sort by end ascending (ties broken by start, then profit — irrelevant to
    # correctness but keeps the order deterministic).
    ordered = sorted(jobs, key=lambda j: (j[1], j[0], j[2]))
    ends = [j[1] for j in ordered]
    n = len(ordered)

    # dp[i] = best profit using only the first i jobs (in end order).
    dp = [0] * (n + 1)
    for i in range(n):
        s, _e, p = ordered[i]
        # Count of already-ordered jobs whose end <= s - gap; those are exactly
        # the jobs that may precede job i under the cooldown rule. Because the
        # array `ends` is sorted, bisect_right gives that count directly, and dp
        # is non-decreasing so dp[k] is the best feasible predecessor profit.
        k = bisect.bisect_right(ends, s - gap)
        take = p + dp[k]
        skip = dp[i]
        dp[i + 1] = take if take > skip else skip

    return dp[n]
