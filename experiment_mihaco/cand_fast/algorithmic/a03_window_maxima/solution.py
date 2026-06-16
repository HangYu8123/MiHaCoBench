from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Return the maximum value in each sliding window of size k.

    Parameters
    ----------
    nums : list[int]
        Input list of integers.
    k : int
        Window size.

    Returns
    -------
    list[int]
        List of length len(nums) - k + 1 with the max of each window.

    Raises
    ------
    ValueError
        If k <= 0.
    """
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k}")

    n = len(nums)

    if k > n:
        return []

    # Monotonic deque storing indices; deque[0] is always the index of the
    # maximum element in the current window.
    dq: deque[int] = deque()
    result: list[int] = []

    for i in range(n):
        # Evict indices that have fallen out of the window on the left.
        if dq and dq[0] <= i - k:
            dq.popleft()

        # Maintain decreasing order: pop from the right while the element at
        # the back of the deque is <= current element (the new element is a
        # better candidate for all future windows).
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()

        dq.append(i)

        # Only start recording results once the first full window is formed.
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
