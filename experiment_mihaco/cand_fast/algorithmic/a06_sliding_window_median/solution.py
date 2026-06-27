import heapq
from collections import defaultdict


def sliding_window_median(nums: list[float], k: int) -> list[float]:
    """Sliding window median in O(n log k) using two heaps with lazy deletion."""
    if k <= 0:
        raise ValueError("k must be a positive integer")
    n = len(nums)
    if k > n:
        return []
    if k == 1:
        return [float(x) for x in nums]

    # lo: max-heap (lower half), stored negated for Python's min-heap
    # hi: min-heap (upper half)
    # Virtual sizes track logical occupancy after lazy deletions.
    # Invariant: lo_size == hi_size + (1 if k is odd else 0)
    lo = []  # negated values
    hi = []
    lo_size = 0  # virtual (logical) size of lo
    hi_size = 0  # virtual (logical) size of hi
    counts = defaultdict(int)  # counts[val] = number of pending lazy deletions

    def _purge_lo():
        """Remove physically stale tops from lo (does NOT adjust lo_size)."""
        while lo and counts[-lo[0]] > 0:
            counts[-lo[0]] -= 1
            if counts[-lo[0]] == 0:
                del counts[-lo[0]]
            heapq.heappop(lo)

    def _purge_hi():
        """Remove physically stale tops from hi (does NOT adjust hi_size)."""
        while hi and counts[hi[0]] > 0:
            counts[hi[0]] -= 1
            if counts[hi[0]] == 0:
                del counts[hi[0]]
            heapq.heappop(hi)

    def rebalance():
        nonlocal lo_size, hi_size
        # Move from lo to hi if lo virtual size is too large
        while lo_size > hi_size + 1:
            _purge_lo()
            val = -heapq.heappop(lo)
            heapq.heappush(hi, val)
            lo_size -= 1
            hi_size += 1
        # Move from hi to lo if hi virtual size is too large
        while hi_size > lo_size:
            _purge_hi()
            val = heapq.heappop(hi)
            heapq.heappush(lo, -val)
            hi_size -= 1
            lo_size += 1

    def push(val):
        """Insert val into the appropriate heap and update virtual size."""
        nonlocal lo_size, hi_size
        _purge_lo()
        if not lo or val <= -lo[0]:
            heapq.heappush(lo, -val)
            lo_size += 1
        else:
            heapq.heappush(hi, val)
            hi_size += 1

    def lazy_delete(val):
        """Mark val as deleted and update virtual size of its owning heap."""
        nonlocal lo_size, hi_size
        # Determine which heap logically owns this value.
        # After purging lo, the lo top is the true maximum of lo.
        _purge_lo()
        if lo and val <= -lo[0]:
            lo_size -= 1
        else:
            hi_size -= 1
        counts[val] += 1

    def get_median():
        """Read current median; purge stale tops first."""
        _purge_lo()
        _purge_hi()
        if k % 2 == 1:
            return float(-lo[0])
        else:
            return (-lo[0] + hi[0]) / 2.0

    # Initialize the first window
    for i in range(k):
        push(float(nums[i]))
    rebalance()

    result = [get_median()]

    # Slide the window
    for i in range(k, n):
        incoming = float(nums[i])
        outgoing = float(nums[i - k])

        # Push incoming element, then lazy-delete outgoing element.
        # After both, rebalance once.
        push(incoming)
        lazy_delete(outgoing)
        rebalance()

        result.append(get_median())

    return result
