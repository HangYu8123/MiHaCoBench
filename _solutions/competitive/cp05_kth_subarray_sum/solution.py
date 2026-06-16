"""Gold reference for competitive/cp05_kth_subarray_sum.

Returns the k-th SMALLEST (1-indexed) sum among all n*(n+1)/2 contiguous-subarray
sums of a non-negative integer array, in O(n log(totalSum)) time.

Algorithm: binary search on the ANSWER.
  * The answer S lies in [min(a), sum(a)]: the smallest possible subarray sum is
    the minimum single element (all elements are non-negative, so no subarray can
    sum to less than the smallest element), and the largest is the whole array.
  * For a candidate threshold S, count how many contiguous subarrays have sum <= S
    using a two-pointer sliding window. This counting is valid PRECISELY because
    every element is non-negative: as the right end advances, the window sum is
    monotonic, so for each right endpoint there is a unique smallest left endpoint
    such that the window sum stays <= S, and every left endpoint at or after it
    also yields a sum <= S. That contributes (right - left + 1) subarrays.
  * The count of subarrays with sum <= S is a non-decreasing step function of S.
    We binary-search for the smallest S with count(<= S) >= k; that S is exactly
    the k-th smallest subarray sum.

Each count pass is O(n); the binary search does O(log(totalSum)) passes, so the
overall cost is O(n log(totalSum)). A naive O(n^2) enumeration of every subarray
sum followed by a sort would enumerate n*(n+1)/2 sums and is far too slow on the
large gate input.
"""
from __future__ import annotations


def kth_subarray_sum(a: list[int], k: int) -> int:
    """Return the k-th smallest contiguous-subarray sum (1-indexed) of ``a``.

    Parameters
    ----------
    a : list[int]
        A list of n >= 1 non-negative integers.
    k : int
        1-indexed rank, with 1 <= k <= n*(n+1)/2.

    Returns
    -------
    int
        The k-th smallest sum among all contiguous subarrays a[i..j] (i <= j).
    """
    n = len(a)
    if n == 1:
        # Only one subarray exists; k must be 1.
        return a[0]

    total = sum(a)
    lo, hi = min(a), total

    def count_le(threshold: int) -> int:
        """Count contiguous subarrays whose sum is <= ``threshold`` (sliding window)."""
        count = 0
        window = 0
        left = 0
        for right in range(n):
            window += a[right]
            # Shrink from the left until the window sum is within the threshold.
            # Monotonic because all elements are non-negative.
            while window > threshold:
                window -= a[left]
                left += 1
            # Every subarray ending at `right` and starting at left..right qualifies.
            count += right - left + 1
        return count

    # Binary search for the smallest S in [lo, hi] with count_le(S) >= k.
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
