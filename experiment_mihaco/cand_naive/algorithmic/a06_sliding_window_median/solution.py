"""
Sliding Window Median — O(n log k) using two heaps with lazy deletion.

Two-heap design:
  lo: max-heap (stored negated) of the lower ceil(k/2) elements
  hi: min-heap of the upper floor(k/2) elements

Invariant: lo_size == target_lo == ceil(k/2), hi_size == floor(k/2).
           max(lo) <= min(hi)

Lazy deletion uses TWO separate counters:
  del_lo[v] = pending removals for value v in the lo heap
  del_hi[v] = pending removals for value v in the hi heap

This separation is critical for correctness when the same value appears in both
heaps simultaneously (which happens with repeated inputs).

Classification of a removed element: compare against the live top of lo
BEFORE marking the element as dead, so pruning does not interfere.
"""

import heapq
from collections import defaultdict


def sliding_window_median(nums: list[float], k: int) -> list[float]:
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k!r}")

    n = len(nums)
    if k > n:
        return []

    lo: list[float] = []   # max-heap via negation
    hi: list[float] = []   # min-heap

    del_lo: dict[float, int] = defaultdict(int)
    del_hi: dict[float, int] = defaultdict(int)

    lo_size: int = 0   # live elements in lo
    hi_size: int = 0   # live elements in hi

    target_lo: int = (k + 1) // 2  # ceil(k/2)

    # ------------------------------------------------------------------ helpers

    def _prune_lo() -> None:
        """Discard dead tops from lo (does not touch lo_size)."""
        while lo and del_lo.get(-lo[0], 0) > 0:
            del_lo[-lo[0]] -= 1
            heapq.heappop(lo)

    def _prune_hi() -> None:
        """Discard dead tops from hi (does not touch hi_size)."""
        while hi and del_hi.get(hi[0], 0) > 0:
            del_hi[hi[0]] -= 1
            heapq.heappop(hi)

    def _lo_top() -> float:
        _prune_lo()
        return -lo[0]

    def _hi_top() -> float:
        _prune_hi()
        return hi[0]

    def _pop_lo() -> float:
        nonlocal lo_size
        _prune_lo()
        lo_size -= 1
        return -heapq.heappop(lo)

    def _pop_hi() -> float:
        nonlocal hi_size
        _prune_hi()
        hi_size -= 1
        return heapq.heappop(hi)

    def _push_lo(val: float) -> None:
        nonlocal lo_size
        heapq.heappush(lo, -val)
        lo_size += 1

    def _push_hi(val: float) -> None:
        nonlocal hi_size
        heapq.heappush(hi, val)
        hi_size += 1

    def _balance() -> None:
        """Restore lo_size == target_lo."""
        while lo_size > target_lo:
            _push_hi(_pop_lo())
        while lo_size < target_lo and hi_size > 0:
            _push_lo(_pop_hi())

    def _add(val: float) -> None:
        """Insert val, routing to the correct heap, then rebalance."""
        # _lo_top() prunes dead tops; val is not dead yet so no interference.
        if lo_size == 0 or val <= _lo_top():
            _push_lo(val)
        else:
            _push_hi(val)
        _balance()

    def _remove(val: float) -> None:
        """Lazily remove val from the window and rebalance.

        We classify val's heap BEFORE marking it dead to avoid the pruning
        bootstrap problem (where val IS the lo top and gets pruned away before
        we can compare against it).
        """
        nonlocal lo_size, hi_size
        # Read live lo top (may prune unrelated dead tops, but not val yet).
        lo_top = _lo_top() if lo_size > 0 else None
        if lo_top is not None and val <= lo_top:
            del_lo[val] += 1
            lo_size -= 1
        else:
            del_hi[val] += 1
            hi_size -= 1
        _balance()

    def _median() -> float:
        if k & 1:
            return float(_lo_top())
        return (_lo_top() + _hi_top()) / 2.0

    # ---------------------------------------------------------------- main loop

    for i in range(k):
        _add(float(nums[i]))

    result: list[float] = [_median()]

    for i in range(k, n):
        _add(float(nums[i]))
        _remove(float(nums[i - k]))
        result.append(_median())

    return result
