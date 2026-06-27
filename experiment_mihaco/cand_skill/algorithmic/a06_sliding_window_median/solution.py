"""
Sliding Window Median — O(n log k) via two heaps with lazy deletion.

Two-heap invariant:
  lo: max-heap (stored negated) holding the lower ceil(k/2) elements
  hi: min-heap holding the upper floor(k/2) elements
  lo_lazy, hi_lazy: separate Counters for pending lazy deletions per heap
  lo_size, hi_size: explicit effective (non-ghost) size trackers (O(1))

Median:
  odd  k -> float(-lo[0])
  even k -> (-lo[0] + hi[0]) / 2.0
"""

import heapq
from collections import Counter


def sliding_window_median(nums: list[float], k: int) -> list[float]:
    # --- Input validation (in priority order) ---
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k}")
    if k > len(nums):
        return []
    if k == 1:
        return [float(x) for x in nums]

    # --- Two heaps with per-heap lazy-deletion counters (DEFECT 3 fix) ---
    lo: list[float] = []   # max-heap (values stored negated)
    hi: list[float] = []   # min-heap
    lo_lazy: Counter = Counter()
    hi_lazy: Counter = Counter()
    lo_size: int = 0   # effective (non-ghost) count in lo
    hi_size: int = 0   # effective (non-ghost) count in hi

    def _clean_lo() -> None:
        """Pop ghost entries from the top of lo."""
        while lo and lo_lazy[-lo[0]]:
            lo_lazy[-lo[0]] -= 1
            heapq.heappop(lo)

    def _clean_hi() -> None:
        """Pop ghost entries from the top of hi."""
        while hi and hi_lazy[hi[0]]:
            hi_lazy[hi[0]] -= 1
            heapq.heappop(hi)

    def _get_median() -> float:
        _clean_lo()
        _clean_hi()
        if k % 2 == 1:
            return float(-lo[0])
        else:
            return (-lo[0] + hi[0]) / 2.0

    def _add(val: float) -> None:
        """Push val into the appropriate heap; update size trackers."""
        nonlocal lo_size, hi_size
        _clean_lo()
        if not lo or val <= -lo[0]:
            heapq.heappush(lo, -val)
            lo_size += 1
        else:
            heapq.heappush(hi, val)
            hi_size += 1

    def _remove(val: float) -> None:
        """
        Mark val as lazily deleted from whichever heap it logically belongs to.
        We determine ownership by comparing val against the current lo max.
        Uses per-heap lazy counters (DEFECT 3 fix: separate counters).
        """
        nonlocal lo_size, hi_size
        _clean_lo()
        _clean_hi()
        if lo and val <= -lo[0]:
            lo_lazy[val] += 1
            lo_size -= 1
        else:
            hi_lazy[val] += 1
            hi_size -= 1

    def _rebalance() -> None:
        """
        Restore invariant after one add + one remove cycle.
        Target: lo_size == ceil(k/2), hi_size == floor(k/2).
        (DEFECT 2 fix: target is k%2 for the difference, not always 0)
        """
        nonlocal lo_size, hi_size
        target_lo = (k + 1) // 2  # ceil(k/2)
        while lo_size > target_lo:
            # lo has too many: move lo's max to hi
            _clean_lo()
            val = -heapq.heappop(lo)
            heapq.heappush(hi, val)
            lo_size -= 1
            hi_size += 1
        while lo_size < target_lo:
            # hi has too many: move hi's min to lo
            _clean_hi()
            val = heapq.heappop(hi)
            heapq.heappush(lo, -val)
            lo_size += 1
            hi_size -= 1

    # --- Initialize first window ---
    for x in nums[:k]:
        _add(float(x))

    # After bulk-adding k elements via _add, rebalance to exact target
    _rebalance()
    result: list[float] = [_get_median()]

    # --- Slide the window ---
    n = len(nums)
    for i in range(k, n):
        outgoing = float(nums[i - k])
        incoming = float(nums[i])

        _add(incoming)
        _remove(outgoing)
        _rebalance()
        result.append(_get_median())

    return result
