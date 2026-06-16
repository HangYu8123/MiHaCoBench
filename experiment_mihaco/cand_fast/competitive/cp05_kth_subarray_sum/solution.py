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

    # Edge case: single element
    if n == 1:
        return int(a[0])

    def count_le(S: int) -> int:
        """Count subarrays with sum <= S using two-pointer sliding window."""
        count = 0
        window_sum = 0
        i = 0
        for j in range(n):
            window_sum += a[j]
            # Shrink window from left while sum exceeds S
            while window_sum > S:
                window_sum -= a[i]
                i += 1
            # All subarrays ending at j and starting from i..j have sum <= S
            count += j - i + 1
        return count

    # Binary search: find smallest S such that count_le(S) >= k
    lo = min(a)
    hi = sum(a)

    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k:
            hi = mid
        else:
            lo = mid + 1

    return int(lo)
