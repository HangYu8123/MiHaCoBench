import bisect


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Select a subset of non-overlapping jobs, respecting a cooldown gap,
    that maximizes total profit. Return the maximum total profit."""
    if not jobs:
        return 0

    # Sort by end time (no mutation of input -- sorted() returns a new list)
    sorted_jobs = sorted(jobs, key=lambda j: j[1])
    n = len(sorted_jobs)

    # Extract end times for binary search
    ends = [j[1] for j in sorted_jobs]

    # best[i] = max profit achievable using any subset of the first i sorted jobs
    # (1-indexed: best[0] = 0, best[i] covers sorted_jobs[0..i-1])
    # This 1-indexed layout avoids the best[-1] Python index trap when j == 0.
    best = [0] * (n + 1)

    for i in range(1, n + 1):
        start_i, end_i, profit_i = sorted_jobs[i - 1]

        # Find the count of compatible predecessor jobs:
        # A predecessor at index k (0-based in sorted_jobs) is compatible iff
        #   sorted_jobs[k].end + gap <= start_i
        #   <=> sorted_jobs[k].end <= start_i - gap
        # bisect_right(ends, start_i - gap) gives exactly that count (call it j).
        # In 1-indexed terms, best[j] is the best profit over those j predecessors.
        j = bisect.bisect_right(ends, start_i - gap)

        # Either skip this job (carry best[i-1]) or take it (best[j] + profit_i)
        best[i] = max(best[i - 1], best[j] + profit_i)

    return best[n]
