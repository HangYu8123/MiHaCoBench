"""
Frequency-tracking LRU Cache — Easy 03.

Eviction policy: Least-Recently-Used (recency only, not frequency).
Each key also stores an access count incremented on every get-hit and put.
"""
from collections import OrderedDict


class FreqLRU:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        self._capacity = capacity
        # Each entry: key -> (value, freq)
        # OrderedDict maintains recency order: MRU at the end (last=True).
        self._cache: OrderedDict = OrderedDict()

    def get(self, key) -> object:
        """Return stored value and increment freq; return None on miss (no state change)."""
        if key not in self._cache:
            return None
        val, freq = self._cache[key]
        self._cache[key] = (val, freq + 1)
        self._cache.move_to_end(key)  # mark as MRU
        return val

    def put(self, key, value) -> None:
        """Insert or update key-value pair; evict LRU if new key and cache is full."""
        if key in self._cache:
            # Update existing key: increment freq, mark MRU, no eviction.
            _, freq = self._cache[key]
            self._cache[key] = (value, freq + 1)
            self._cache.move_to_end(key)
        else:
            # New key: evict LRU if at capacity.
            if len(self._cache) >= self._capacity:
                self._cache.popitem(last=False)  # remove LRU (front)
            self._cache[key] = (value, 1)
            # New keys are appended at the end (MRU position) by default.

    def histogram(self) -> dict:
        """Return a plain dict mapping each resident key to its access count."""
        return {k: v[1] for k, v in self._cache.items()}

    def __len__(self) -> int:
        return len(self._cache)
