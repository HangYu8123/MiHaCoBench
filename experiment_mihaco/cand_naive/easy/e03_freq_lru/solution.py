"""
Easy 03 — freq_lru: Frequency-tracking LRU Cache

Uses OrderedDict from collections to maintain LRU order efficiently.
"""

from collections import OrderedDict


class FreqLRU:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._capacity = capacity
        # OrderedDict preserves insertion order; we move items to end on access
        # keys -> values
        self._cache: OrderedDict = OrderedDict()
        # keys -> access counts (only for currently resident keys)
        self._freq: dict = {}

    def get(self, key) -> object:
        """Return value for key on hit (and update recency/freq), None on miss."""
        if key not in self._cache:
            return None
        # Hit: increment freq and mark as most-recently-used
        self._freq[key] += 1
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key, value) -> None:
        """Insert or update key-value pair with LRU eviction when at capacity."""
        if key in self._cache:
            # Existing key: update value, increment freq, mark MRU
            self._cache[key] = value
            self._freq[key] += 1
            self._cache.move_to_end(key)
        else:
            # New key
            if len(self._cache) >= self._capacity:
                # Evict LRU (first item in OrderedDict)
                evicted_key, _ = self._cache.popitem(last=False)
                del self._freq[evicted_key]
            # Insert new key with freq=1 as MRU (at end)
            self._cache[key] = value
            self._freq[key] = 1

    def histogram(self) -> dict:
        """Return dict mapping currently cached keys to their access counts."""
        return dict(self._freq)

    def __len__(self) -> int:
        """Return number of keys currently in the cache."""
        return len(self._cache)
