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
    O(n log n) using DP + binary search (sort by end time, bisect for the latest
    compatible predecessor).
    """
    if not jobs:
        return 0

    # Sort jobs by end time (ascending) to establish DP ordering invariant.
    sorted_jobs = sorted(jobs, key=lambda j: j[1])

    n = len(sorted_jobs)
    # Build list of end times for binary search.
    ends = [job[1] for job in sorted_jobs]

    # dp[i] = max profit using only the first i jobs (0..i-1 in sorted_jobs).
    # dp[0] = 0 means we selected no jobs.
    dp = [0] * (n + 1)

    for i in range(1, n + 1):
        start, end, profit = sorted_jobs[i - 1]
        # Find the count of jobs (in sorted order) whose end <= start.
        # bisect_right(ends, start) gives the rightmost insertion point for start,
        # which equals the count of elements <= start in ends.
        # Since compatibility is next.start >= prev.end, a job ending exactly at
        # `start` is compatible (not conflicting), so we include it.
        p = bisect.bisect_right(ends, start)
        # Option 1: skip this job (take dp[i-1]).
        # Option 2: take this job (dp[p] + profit).
        dp[i] = max(dp[i - 1], dp[p] + profit)

    return dp[n]
