def kth_subarray_sum(a: list[int], k: int) -> int:
    """Return the k-th SMALLEST contiguous-subarray sum (1-indexed) of `a`.

    Parameters
    ----------
    a : list[int]
        A list of n >= 1 NON-NEGATIVE integers (values may be 0).
    k : int
        A 1-indexed rank, with 1 <= k <= n*(n+1)/2.

    Returns
    -------
    int
        The k-th smallest value among ALL n*(n+1)/2 contiguous-subarray sums.
    """
    n = len(a)

    def count_le(S: int) -> int:
        """Count subarrays with sum <= S using two-pointer sliding window."""
        count = 0
        window_sum = 0
        i = 0
        for j in range(n):
            window_sum += a[j]
            while window_sum > S:
                window_sum -= a[i]
                i += 1
            count += j - i + 1
        return count

    lo = min(a)
    hi = sum(a)

    # Binary search: find smallest S such that count_le(S) >= k.
    # Invariant: answer is in [lo, hi].
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k:
            hi = mid
        else:
            lo = mid + 1

    return lo
