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

    # Handle trivial case
    if n == 1:
        return a[0]

    def count_le(target: int) -> int:
        """Count subarrays with sum <= target using two-pointer sliding window.

        Because all elements are non-negative, extending the window (moving right)
        monotonically increases the sum, and shrinking from the left monotonically
        decreases it. This allows an O(n) two-pointer approach.
        """
        count = 0
        window_sum = 0
        left = 0
        for right in range(n):
            window_sum += a[right]
            # Shrink window from left while sum exceeds target
            while window_sum > target and left <= right:
                window_sum -= a[left]
                left += 1
            # All subarrays ending at 'right' with start in [left, right] are valid
            count += (right - left + 1)
        return count

    lo = min(a)
    hi = sum(a)

    # Binary search for the smallest S such that count_le(S) >= k
    # The answer must be an actual subarray sum that appears in the array.
    # Since all values are non-negative integers, we binary search over integers.
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k:
            hi = mid
        else:
            lo = mid + 1

    return lo
