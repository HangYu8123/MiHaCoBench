import bisect


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Select a subset of non-overlapping jobs, respecting a cooldown gap,
    that maximizes total profit. Return the maximum total profit."""
    if not jobs:
        return 0

    # Sort a copy by end time (ascending); do not mutate input
    sorted_jobs = sorted(jobs, key=lambda j: j[1])
    n = len(sorted_jobs)

    # Build sorted ends array (0-indexed) from sorted jobs
    ends = [j[1] for j in sorted_jobs]

    # dp[i] = max profit considering first i jobs (1-indexed), dp[0] = 0
    # prefix_max[i] = max(dp[0..i])
    dp = [0] * (n + 1)
    prefix_max = [0] * (n + 1)

    for i in range(1, n + 1):
        start, end, profit = sorted_jobs[i - 1]

        # Find largest j such that ends[j-1] + gap <= start
        # i.e., ends[j-1] <= start - gap
        # bisect_right(ends, start - gap, 0, i-1) gives count of jobs
        # in ends[0..i-2] where end <= start - gap, which is our DP index j
        j = bisect.bisect_right(ends, start - gap, 0, i - 1)

        # Either skip job i (dp[i-1]) or take job i (prefix_max[j] + profit)
        dp[i] = max(dp[i - 1], prefix_max[j] + profit)
        prefix_max[i] = max(prefix_max[i - 1], dp[i])

    return dp[n]
