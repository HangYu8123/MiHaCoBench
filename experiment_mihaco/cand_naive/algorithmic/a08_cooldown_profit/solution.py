"""
Algorithmic 08 — max_profit: weighted interval scheduling with a mandatory cooldown gap.

Algorithm: O(n log n) DP with binary search.
1. Sort jobs by end time.
2. For each job i (sorted by end), compute dp[i] = best profit using jobs from [0..i]
   where job i is included.
   - We need the best dp[j] for all j where jobs[j].end + gap <= jobs[i].start.
   - We use bisect to find the last eligible job, plus a prefix-maximum array to get
     the best value in O(1) after the binary search.
3. Answer is the maximum over all dp[i] (and 0 for empty).
"""

import bisect


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Select a subset of non-overlapping jobs, respecting a cooldown gap,
    that maximizes total profit. Return the maximum total profit."""
    if not jobs:
        return 0

    # Sort by end time (do not mutate input)
    sorted_jobs = sorted(jobs, key=lambda j: j[1])
    n = len(sorted_jobs)

    # Extract end times for binary search
    ends = [j[1] for j in sorted_jobs]

    # dp[i] = maximum profit of a valid schedule where job i is the LAST selected job
    dp = [0] * n

    # prefix_max[i] = max(dp[0], dp[1], ..., dp[i])
    # We build this as we go.
    prefix_max = [0] * n

    for i in range(n):
        start_i, end_i, profit_i = sorted_jobs[i]

        # Find the last job j such that ends[j] + gap <= start_i
        # i.e., ends[j] <= start_i - gap
        # We want the rightmost j with ends[j] <= start_i - gap
        # bisect_right(ends, start_i - gap) - 1 gives the index of the last element <= target
        target = start_i - gap
        pos = bisect.bisect_right(ends, target) - 1

        if pos < 0:
            # No compatible earlier job; just take this job alone
            dp[i] = profit_i
        else:
            # Best profit from any compatible earlier ending job + profit_i
            dp[i] = prefix_max[pos] + profit_i

        # Update prefix max
        if i == 0:
            prefix_max[i] = dp[i]
        else:
            prefix_max[i] = max(prefix_max[i - 1], dp[i])

    return prefix_max[n - 1]
