import bisect


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Select a subset of non-overlapping jobs, respecting a cooldown gap,
    that maximizes total profit. Return the maximum total profit."""
    if not jobs:
        return 0

    # Sort jobs by end time
    sorted_jobs = sorted(jobs, key=lambda j: j[1])
    n = len(sorted_jobs)

    # ends[i] = end time of the i-th job (0-indexed, after sorting)
    ends = [j[1] for j in sorted_jobs]

    # dp[i] = best profit considering jobs 0..i-1 (first i jobs)
    # dp[0] = 0 (no jobs selected)
    # dp[i+1] = max(dp[i],   # skip job i
    #               sorted_jobs[i][2] + best_dp_ending_before_start_i - gap)
    # We need max dp[k] for all k where ends[k-1] + gap <= start_i
    # i.e., ends[k-1] <= start_i - gap
    # i.e., the latest job we can take ends at start_i - gap or earlier

    # We maintain prefix_max[i] = max(dp[0], dp[1], ..., dp[i])
    # To find best dp for jobs ending <= threshold:
    #   find largest index k where ends[k-1] <= threshold (i.e., ends[k] <= threshold for 1-indexed ends array)
    #   use prefix_max[k]

    dp = [0] * (n + 1)
    prefix_max = [0] * (n + 1)

    for i in range(n):
        start_i, end_i, profit_i = sorted_jobs[i]
        # We need the best dp[k] where k corresponds to jobs with end <= start_i - gap
        # ends array is 0-indexed: ends[j] = end of job j
        # dp[k] represents profit using first k jobs (jobs 0..k-1)
        # dp[k] considers job k-1 as the last one we might choose
        # We want jobs ending at or before (start_i - gap)
        threshold = start_i - gap
        # Find rightmost index in ends where ends[idx] <= threshold
        # bisect_right returns insertion point for threshold+1, so all values <= threshold are at indices < that
        # ends is sorted since we sorted by end time
        # We want: largest j such that ends[j] <= threshold (0-indexed job index)
        # That corresponds to dp[j+1] being available
        # Using bisect_right: idx = bisect_right(ends, threshold) gives # of jobs with end <= threshold
        # So dp[idx] is the best we can use (taking first idx jobs into account)
        idx = bisect.bisect_right(ends, threshold)
        # prefix_max[idx] = max(dp[0], ..., dp[idx])
        best_before = prefix_max[idx]

        # Option 1: skip job i
        # Option 2: take job i
        dp[i + 1] = max(dp[i], best_before + profit_i)
        prefix_max[i + 1] = max(prefix_max[i], dp[i + 1])

    return dp[n]
