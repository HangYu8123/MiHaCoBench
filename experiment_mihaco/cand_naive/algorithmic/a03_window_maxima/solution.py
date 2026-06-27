from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Return the maximum of each sliding window of size k over nums.

    Uses a monotonic deque to achieve O(n) time and O(k) space.

    Parameters
    ----------
    nums : list[int]
        Input list of integers.
    k : int
        Window size.

    Returns
    -------
    list[int]
        List of length len(nums) - k + 1 containing window maxima.

    Raises
    ------
    ValueError
        If k <= 0.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    n = len(nums)

    if k > n:
        return []

    # Monotonic deque stores indices of elements in decreasing order of value.
    # Front of deque is always the index of the current window's maximum.
    dq: deque[int] = deque()
    result: list[int] = []

    for i in range(n):
        # Remove indices that are no longer in the window (left boundary expired)
        while dq and dq[0] < i - k + 1:
            dq.popleft()

        # Maintain decreasing monotonic order: remove all indices whose
        # corresponding values are <= nums[i], since they can never be
        # the maximum for any future window while nums[i] is still in range.
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()

        dq.append(i)

        # Once we have processed at least k elements, record the maximum
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
