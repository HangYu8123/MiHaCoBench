"""
k-th Smallest Contiguous-Subarray Sum

Algorithm: O(n * log(totalSum))
- Binary search over the answer S in [min(a), sum(a)]
- For each candidate S, count subarrays with sum <= S using two-pointer sliding window
  (valid because all elements are non-negative, so window sums are monotonic)
- Return the smallest S such that count(sum <= S) >= k
"""


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
        return a[0]

    lo = min(a)
    hi = sum(a)

    def count_le(target: int) -> int:
        """Count number of contiguous subarrays with sum <= target."""
        count = 0
        window_sum = 0
        left = 0
        for right in range(n):
            window_sum += a[right]
            # Shrink window from left while window_sum > target
            while window_sum > target and left <= right:
                window_sum -= a[left]
                left += 1
            # All subarrays ending at `right` and starting from left..right
            # have sum <= target
            count += right - left + 1
        return count

    # Binary search for the smallest S such that count_le(S) >= k
    # lo and hi bracket the answer: count_le(lo) might be < k, count_le(hi) == total >= k
    # We want smallest S in [lo, hi] with count_le(S) >= k
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k:
            hi = mid
        else:
            lo = mid + 1

    return lo
