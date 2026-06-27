"""
Easy 03 — FreqLRU: Frequency-tracking LRU Cache
Eviction policy: pure LRU (recency only); frequency is stored for histogram only.
"""
from collections import OrderedDict


class FreqLRU:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        self._capacity = capacity
        # Each value: [stored_value, access_count]
        # OrderedDict maintains insertion/recency order:
        #   move_to_end(key)         → marks key as MRU (rightmost)
        #   popitem(last=False)      → evicts LRU (leftmost)
        self._cache: OrderedDict = OrderedDict()

    def __len__(self) -> int:
        return len(self._cache)

    def get(self, key) -> object:
        """
        Hit: increment access count, mark MRU, return value.
        Miss: return None, no state change.
        """
        if key not in self._cache:
            return None
        self._cache[key][1] += 1
        self._cache.move_to_end(key)        # mark as most-recently-used
        return self._cache[key][0]

    def put(self, key, value) -> None:
        """
        Existing key: update value, increment freq, mark MRU.
        New key, capacity not full: insert with freq=1, mark MRU.
        New key, at capacity: evict LRU first, then insert with freq=1.
        """
        if key in self._cache:
            self._cache[key][0] = value
            self._cache[key][1] += 1
            self._cache.move_to_end(key)    # mark as most-recently-used
        else:
            if len(self._cache) == self._capacity:
                self._cache.popitem(last=False)   # evict least-recently-used
            self._cache[key] = [value, 1]
            self._cache.move_to_end(key)    # ensure at MRU end (harmless; new key already there)

    def histogram(self) -> dict:
        """Return {key: access_count} for every key currently in the cache."""
        return {k: v[1] for k, v in self._cache.items()}
