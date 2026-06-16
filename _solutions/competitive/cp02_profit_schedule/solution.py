"""Gold reference for competitive/cp02_profit_schedule.

Weighted Interval Scheduling via DP + binary search.
Time complexity: O(n log n) — sort by end time, then for each job binary-search
for the latest non-conflicting predecessor using bisect_right.

Contract: max_profit(jobs) -> int  (>= 0)
"""
from __future__ import annotations

import bisect


def max_profit(jobs: list[tuple[int, int, int]]) -> int:
    """Return the maximum total profit from a non-overlapping subset of jobs.

    Two jobs are compatible when next.start >= prev.end (adjacency is allowed).
    Profits may be negative; such jobs are never beneficial and will be skipped
    naturally by the DP (the 0 base-case ensures we never go below 0).
    """
    if not jobs:
        return 0

    # Sort by end time (primary); ties broken arbitrarily.
    sorted_jobs = sorted(jobs, key=lambda j: (j[1], j[0]))

    n = len(sorted_jobs)
    ends = [j[1] for j in sorted_jobs]   # end times of sorted jobs

    # dp[i] = best profit considering jobs 0..i-1
    # dp[0] = 0  (no jobs selected)
    # dp[i] = max(dp[i-1],                              # skip job i-1
    #             dp[p] + sorted_jobs[i-1][2])          # take job i-1
    # where p = latest index whose job ends <= sorted_jobs[i-1].start
    dp = [0] * (n + 1)

    for i in range(1, n + 1):
        start_i, end_i, profit_i = sorted_jobs[i - 1]

        # Find the rightmost job (index j, 0-based) whose end <= start_i.
        # bisect_right on ends (0-based) gives the insertion point for start_i;
        # all indices < that point have end <= start_i (compatible predecessor).
        # We search in ends[:i-1] (jobs before current) — but since ends is sorted
        # we can just bisect in the full ends array up to i-1.
        p = bisect.bisect_right(ends, start_i, 0, i - 1)
        # dp[p] is the best profit using only the first p jobs (all end <= start_i)
        dp[i] = max(dp[i - 1], dp[p] + profit_i)

    return dp[n]
