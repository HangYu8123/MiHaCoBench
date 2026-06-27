from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    if k <= 0:
        raise ValueError("k must be positive")
    if k > len(nums):
        return []
    dq = deque()
    result = []
    for i, val in enumerate(nums):
        # evict indices outside the current window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        # maintain strictly decreasing invariant (pop equal or smaller values)
        while dq and nums[dq[-1]] <= val:
            dq.pop()
        dq.append(i)
        # append max once the first full window is formed
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
