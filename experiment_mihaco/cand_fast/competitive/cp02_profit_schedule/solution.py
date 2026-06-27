from bisect import bisect_right


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
    O(n log n) — sort by end time + DP with binary search for latest compatible
    predecessor.
    """
    if not jobs:
        return 0

    # Sort jobs by end time ascending
    sorted_jobs = sorted(jobs, key=lambda j: j[1])
    n = len(sorted_jobs)

    # Build array of end times for binary search (0-indexed, parallel to sorted_jobs)
    ends = [job[1] for job in sorted_jobs]

    # dp[i] = max profit considering first i jobs (1-indexed), dp[0] = 0 (base case)
    dp = [0] * (n + 1)

    for i in range(1, n + 1):
        start, end, profit = sorted_jobs[i - 1]

        # Find the rightmost job whose end <= start of current job (compatible predecessor).
        # bisect_right on ends[0..i-1] gives the count of ends <= start,
        # which is exactly the index j into dp for the best compatible predecessor.
        # We restrict the search to the first i-1 entries (index 0..i-2) so we
        # never consider the current job itself.
        j = bisect_right(ends, start, 0, i - 1)

        # Skip current job (dp[i-1]) vs. take current job (dp[j] + profit)
        dp[i] = max(dp[i - 1], dp[j] + profit)

    return dp[n]
