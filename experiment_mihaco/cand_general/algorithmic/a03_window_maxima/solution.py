from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Return the maximum value in each sliding window of size k.

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
        List of length len(nums) - k + 1 with the maximum per window.

    Raises
    ------
    ValueError
        If k <= 0.
    """
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k}")

    if k > len(nums):
        return []

    # Deque stores indices; invariant: values at those indices are
    # strictly decreasing from front to back. The front always holds
    # the index of the current window's maximum.
    dq: deque[int] = deque()
    result: list[int] = []

    for i in range(len(nums)):
        # Remove from back any index whose value is <= current value.
        # Using <= so that duplicate values collapse to the rightmost
        # index (keeps the deque minimal in size).
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()

        dq.append(i)

        # Evict the front if it has fallen outside the current window.
        # Window spans [i - k + 1, i], so any index < i - k + 1 is stale.
        while dq[0] < i - k + 1:
            dq.popleft()

        # The window is complete once we have seen at least k elements.
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
