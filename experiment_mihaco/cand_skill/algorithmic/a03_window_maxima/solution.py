from collections import deque


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Return the maximum value in each sliding window of size k.

    Time:  O(n)  — each index is pushed and popped at most once.
    Space: O(k)  — the deque holds at most k indices at any time.

    Raises ValueError if k <= 0.
    Returns [] if k > len(nums).
    """
    if k <= 0:
        raise ValueError("k must be a positive integer")
    if k > len(nums):
        return []

    dq: deque[int] = deque()  # stores indices; front = index of current max
    result: list[int] = []

    for i in range(len(nums)):
        # Evict from the right any index whose value is <= nums[i]
        # (they can never be the maximum while nums[i] is in the window)
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()

        dq.append(i)

        # Evict from the left any index that has fallen outside the window
        # Window is [i-k+1 .. i], so index i-k is the first stale index
        if dq[0] <= i - k:
            dq.popleft()

        # Start emitting results once the first full window is complete
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result


if __name__ == "__main__":
    # --- Canonical example ---
    assert window_maxima([1, 3, -1, -3, 5, 3, 6, 7], k=3) == [3, 3, 5, 5, 6, 7]

    # --- Edge cases ---
    # k == 1: return a copy of nums
    assert window_maxima([4, 2, 7], k=1) == [4, 2, 7]
    assert window_maxima([5], k=1) == [5]

    # k == len(nums): return [max(nums)]
    assert window_maxima([2, 1], k=2) == [2]
    assert window_maxima([1, 2, 3], k=3) == [3]

    # k > len(nums): return []
    assert window_maxima([], k=1) == []
    assert window_maxima([1, 2], k=5) == []

    # k <= 0: raise ValueError
    try:
        window_maxima([1, 2, 3], k=0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        window_maxima([1, 2, 3], k=-1)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Negative, zero, repeated elements
    assert window_maxima([-3, -1, -2], k=2) == [-1, -1]
    assert window_maxima([0, 0, 0], k=2) == [0, 0]
    assert window_maxima([5, 5, 5, 5], k=3) == [5, 5]

    # Single element, k == 1
    assert window_maxima([42], k=1) == [42]

    # Large monotonically decreasing input (stress boundary check)
    n = 1_000_000
    large = list(range(n, 0, -1))
    out = window_maxima(large, k=1000)
    assert len(out) == n - 1000 + 1
    assert out[0] == n       # first window max
    assert out[-1] == 1000   # last window max

    print("All assertions passed.")
