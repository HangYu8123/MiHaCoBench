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

    def count_le(nums: list[int], S: int) -> int:
        """Count number of contiguous subarrays with sum <= S.

        Uses two-pointer sliding window (O(n)). Valid because all elements
        are non-negative, so window sums are monotonically non-decreasing as
        the right pointer advances — shrinking from the left always reduces sum.
        """
        count = 0
        window_sum = 0
        left = 0
        for right, num in enumerate(nums):
            window_sum += num
            # Shrink from left while window sum exceeds S
            while window_sum > S:
                window_sum -= nums[left]
                left += 1
            # All subarrays ending at `right` with left endpoint in [left, right]
            count += right - left + 1
        return count

    # Binary search over the integer range [min(a), sum(a)]
    # Find the smallest S such that count_le(a, S) >= k
    # This is exactly the k-th smallest subarray sum because:
    #   - count_le is a non-decreasing step function of S
    #   - It jumps only at actual subarray-sum values
    #   - The leftmost S where count >= k is that k-th value
    lo = min(a)
    hi = sum(a)

    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(a, mid) >= k:
            hi = mid
        else:
            lo = mid + 1

    return int(lo)


if __name__ == "__main__":
    # TDD: verify against all spec examples before finalizing
    assert kth_subarray_sum([7], 1) == 7, "single element"
    assert kth_subarray_sum([1, 2, 3], 1) == 1, "[1,2,3] k=1"
    assert kth_subarray_sum([1, 2, 3], 4) == 3, "[1,2,3] k=4"
    assert kth_subarray_sum([1, 2, 3], 6) == 6, "[1,2,3] k=6"
    assert kth_subarray_sum([2, 2, 2], 3) == 2, "[2,2,2] k=3"
    assert kth_subarray_sum([2, 2, 2], 5) == 4, "[2,2,2] k=5"
    assert kth_subarray_sum([0, 0, 5], 1) == 0, "[0,0,5] k=1"
    assert kth_subarray_sum([0, 0, 5], 4) == 5, "[0,0,5] k=4"

    # count_le helper unit tests
    def count_le(nums, S):
        count = window_sum = left = 0
        for right, num in enumerate(nums):
            window_sum += num
            while window_sum > S:
                window_sum -= nums[left]
                left += 1
            count += right - left + 1
        return count

    assert count_le([1, 2, 3], 3) == 4, "count_le [1,2,3] S=3"
    assert count_le([1, 2, 3], 0) == 0, "count_le [1,2,3] S=0"

    print("All tests passed.")
