"""Gold reference for algorithmic/a06_sliding_window_median.

Sliding-window median using two heaps (max-heap for lower half, min-heap for
upper half) with lazy deletion.

Time complexity:  O(n log k)
Space complexity: O(k)
"""
from __future__ import annotations

import heapq
from collections import defaultdict


def sliding_window_median(nums: list[float], k: int) -> list[float]:
    """Return the median of every contiguous window of size k.

    Parameters
    ----------
    nums:
        Input list of numbers.
    k:
        Window size.

    Returns
    -------
    list[float]
        Medians for each window in left-to-right order.
        Length = len(nums) - k + 1 for valid k, or [] when k > len(nums).

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

    # lo is a max-heap (negate values) holding the lower half of the window.
    # hi is a min-heap holding the upper half of the window.
    # Invariants maintained after rebalance:
    #   len_lo == (k + 1) // 2  (ceil(k/2))
    #   len_hi == k // 2        (floor(k/2))
    #   all elements in lo <= all elements in hi
    #
    # Median:
    #   odd k  -> -lo[0]
    #   even k -> (-lo[0] + hi[0]) / 2

    lo: list[float] = []   # max-heap via negation; real size tracked by len_lo
    hi: list[float] = []   # min-heap; real size tracked by len_hi

    # lazy_del[x] counts pending virtual removals of value x.
    lazy_del: dict[float, int] = defaultdict(int)

    # Effective (non-deleted) sizes.
    len_lo: int = 0
    len_hi: int = 0

    def _purge_lo_top() -> None:
        """Remove lazily-deleted entries from the top of the lo heap."""
        while lo and lazy_del[-lo[0]]:
            lazy_del[-lo[0]] -= 1
            heapq.heappop(lo)

    def _purge_hi_top() -> None:
        """Remove lazily-deleted entries from the top of the hi heap."""
        while hi and lazy_del[hi[0]]:
            lazy_del[hi[0]] -= 1
            heapq.heappop(hi)

    def _push_lo(val: float) -> None:
        nonlocal len_lo
        heapq.heappush(lo, -val)
        len_lo += 1

    def _push_hi(val: float) -> None:
        nonlocal len_hi
        heapq.heappush(hi, val)
        len_hi += 1

    def _pop_lo() -> float:
        """Pop and return the true maximum from the lo heap."""
        nonlocal len_lo
        _purge_lo_top()
        val = -heapq.heappop(lo)
        len_lo -= 1
        return val

    def _pop_hi() -> float:
        """Pop and return the true minimum from the hi heap."""
        nonlocal len_hi
        _purge_hi_top()
        val = heapq.heappop(hi)
        len_hi -= 1
        return val

    def _rebalance() -> None:
        """Ensure lo holds ceil(k/2) elements and hi holds floor(k/2) elements,
        and that lo's max <= hi's min.
        """
        nonlocal len_lo, len_hi
        target_lo = (k + 1) // 2
        target_hi = k // 2

        # First fix the cross-heap ordering invariant by swapping tops if needed.
        _purge_lo_top()
        _purge_hi_top()
        if lo and hi and (-lo[0]) > hi[0]:
            lo_top = _pop_lo()
            hi_top = _pop_hi()
            _push_lo(hi_top)
            _push_hi(lo_top)

        # Now rebalance sizes.
        while len_lo > target_lo:
            _push_hi(_pop_lo())
        while len_hi > target_hi:
            _push_lo(_pop_hi())

        # Check ordering again after size rebalancing.
        _purge_lo_top()
        _purge_hi_top()
        if lo and hi and (-lo[0]) > hi[0]:
            lo_top = _pop_lo()
            hi_top = _pop_hi()
            _push_lo(hi_top)
            _push_hi(lo_top)

    def _get_median() -> float:
        """Return the current window median."""
        _purge_lo_top()
        if k % 2 == 1:
            return float(-lo[0])
        _purge_hi_top()
        return (-lo[0] + hi[0]) / 2.0

    result: list[float] = []

    # Seed the first window.
    for i in range(k):
        val = float(nums[i])
        _purge_lo_top()
        if len_lo == 0 or val <= -lo[0]:
            _push_lo(val)
        else:
            _push_hi(val)
        _rebalance()

    result.append(_get_median())

    # Slide the window one step at a time.
    for i in range(k, n):
        incoming = float(nums[i])
        outgoing = float(nums[i - k])

        # Determine which heap contains outgoing and adjust effective size.
        _purge_lo_top()
        if lo and outgoing <= -lo[0]:
            lazy_del[outgoing] += 1
            len_lo -= 1
        else:
            lazy_del[outgoing] += 1
            len_hi -= 1

        # Insert incoming element into the appropriate heap.
        _purge_lo_top()
        if len_lo == 0 or incoming <= -lo[0]:
            _push_lo(incoming)
        else:
            _push_hi(incoming)

        _rebalance()
        result.append(_get_median())

    return result
