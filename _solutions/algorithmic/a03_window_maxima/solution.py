"""Gold reference for algorithmic/a03_window_maxima.

Implements the classic O(n) monotonic-deque sliding-window maximum algorithm.
The deque stores indices of *potentially useful* elements in decreasing-value
order.  Each index is added once and removed at most once, so the overall
complexity is O(n) time and O(k) space.
"""
from __future__ import annotations

from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Return the maximum of every contiguous window of size *k* in *nums*.

    Parameters
    ----------
    nums:
        Input list of integers.
    k:
        Window size.  Must be >= 1.

    Returns
    -------
    list[int]
        A list of length ``len(nums) - k + 1`` containing the window maxima in
        left-to-right order.  Returns ``[]`` when ``k > len(nums)``.

    Raises
    ------
    ValueError
        If ``k <= 0``.
    """
    if k <= 0:
        raise ValueError(f"window size k must be >= 1, got {k}")

    n = len(nums)
    if k > n:
        return []

    result: list[int] = []
    # dq holds indices; front is always the index of the current window maximum.
    # Indices in dq are in increasing order; corresponding values are decreasing.
    dq: deque[int] = deque()

    for i, val in enumerate(nums):
        # Remove indices that have fallen out of the current window.
        while dq and dq[0] < i - k + 1:
            dq.popleft()

        # Maintain the decreasing-value invariant: discard any index at the back
        # whose value is <= the current value (it can never be a future maximum).
        while dq and nums[dq[-1]] <= val:
            dq.pop()

        dq.append(i)

        # The window is complete once we have processed at least k elements.
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
