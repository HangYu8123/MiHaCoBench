"""
Algorithmic 08 — max_profit: weighted interval scheduling with a mandatory cooldown gap.

Algorithm: O(n log n) DP with binary search + prefix maximum.
1. Sort jobs by end time (copy, no mutation).
2. For each job i, binary-search for the rightmost predecessor j where end_j + gap <= start_i.
3. DP recurrence: dp[i] = max(profit_i + best_up_to_j, best_up_to_{i-1}).
4. Maintain prefix_max for O(1) lookup of best profit among all predecessors.
"""

import bisect


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Select a subset of non-overlapping jobs, respecting a cooldown gap,
    that maximizes total profit. Return the maximum total profit."""
    if not jobs:
        return 0

    # Sort by end time (do not mutate input)
    jobs_sorted = sorted(jobs, key=lambda j: j[1])
    n = len(jobs_sorted)

    # Extract end times for binary search
    end_times = [j[1] for j in jobs_sorted]

    # dp[i] = best profit considering jobs_sorted[0..i] where job i is taken
    # prefix_max[i] = max(dp[0], dp[1], ..., dp[i]) — best profit up to index i
    dp = [0] * n
    prefix_max = [0] * n

    for i in range(n):
        start_i = jobs_sorted[i][0]
        profit_i = jobs_sorted[i][2]

        # Find rightmost j such that end_times[j] + gap <= start_i
        # i.e., end_times[j] <= start_i - gap
        # bisect_right returns insertion point for (start_i - gap), so index - 1 is the answer
        threshold = start_i - gap
        j = bisect.bisect_right(end_times, threshold, 0, i) - 1

        # Profit if we take job i
        best_predecessor = prefix_max[j] if j >= 0 else 0
        take = profit_i + best_predecessor

        # Profit if we skip job i (best so far without taking job i)
        skip = prefix_max[i - 1] if i > 0 else 0

        dp[i] = max(take, skip)
        prefix_max[i] = max(prefix_max[i - 1] if i > 0 else 0, dp[i])

    return prefix_max[n - 1]
