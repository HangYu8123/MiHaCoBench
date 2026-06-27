import bisect


def max_profit(jobs: list[tuple[int, int, int]]) -> int:
    """Return the maximum total profit from a non-overlapping subset of jobs.

    Parameters
    ----------
    jobs : list of (start, end, profit) tuples
        Each entry is (start: int, end: int, profit: int).
        Jobs where end <= start are invalid and will not appear in test inputs.
        Profits may be negative (such jobs should simply not be selected).

    Returns
    -------
    int
        Maximum achievable total profit. Returns 0 if no profitable selection exists
        (e.g., all profits are negative, or jobs is empty).

    Complexity
    ----------
    O(n log n) — sort by end time, DP with binary search for latest compatible predecessor.
    """
    if not jobs:
        return 0

    # Sort jobs by end time
    sorted_jobs = sorted(jobs, key=lambda j: j[1])

    n = len(sorted_jobs)
    # dp[i] = maximum profit considering jobs 0..i-1 (i jobs)
    dp = [0] * (n + 1)

    # Store end times for binary search
    end_times = [j[1] for j in sorted_jobs]

    for i in range(1, n + 1):
        start, end, profit = sorted_jobs[i - 1]

        # Find the latest job that ends <= start (compatible predecessor)
        # bisect_right gives index of first end_time > start, so index-1 is latest compatible
        # We need end_time <= start, i.e., bisect_right(end_times, start) in end_times[0..i-1]
        idx = bisect.bisect_right(end_times, start, 0, i - 1)
        # idx is the number of compatible predecessors (those ending <= start)
        # dp[idx] is the max profit from those jobs

        # Option 1: skip this job → dp[i-1]
        # Option 2: take this job → dp[idx] + profit (only if profit > 0, but DP handles this)
        take = dp[idx] + profit
        skip = dp[i - 1]
        dp[i] = max(skip, take)

    return max(0, dp[n])
