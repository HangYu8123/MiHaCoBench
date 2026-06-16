from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    """
    Compute the maximum value in each sliding window of size k using a monotonic deque.

    Parameters
    ----------
    nums : list[int]
        Input list of integers.
    k : int
        Window size.

    Returns
    -------
    list[int]
        List of length len(nums) - k + 1 containing the maximum in each window.

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

    # Deque stores indices; front always holds index of the max element in the current window.
    # Elements in the deque are maintained in decreasing order of their nums values.
    dq: deque[int] = deque()
    result: list[int] = []

    for i in range(n):
        # Remove indices that are out of the current window's left boundary.
        while dq and dq[0] < i - k + 1:
            dq.popleft()

        # Remove indices from the back whose corresponding values are <= nums[i].
        # They can never be the maximum while nums[i] is in the window.
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()

        dq.append(i)

        # Start recording results once the first full window is complete.
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
