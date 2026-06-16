"""
Easy 03 — freq_lru: Frequency-tracking LRU Cache
Standard library only.
"""
from collections import OrderedDict


class FreqLRU:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        self._capacity = capacity
        self._cache: OrderedDict = OrderedDict()
        self._freq: dict = {}

    def get(self, key) -> object:
        if key not in self._cache:
            return None
        self._freq[key] += 1
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key, value) -> None:
        if key in self._cache:
            self._cache[key] = value
            self._freq[key] += 1
            self._cache.move_to_end(key)
        else:
            if len(self._cache) == self._capacity:
                evicted, _ = self._cache.popitem(last=False)
                del self._freq[evicted]
            self._cache[key] = value
            self._freq[key] = 1
            self._cache.move_to_end(key)

    def histogram(self) -> dict:
        return dict(self._freq)

    def __len__(self) -> int:
        return len(self._cache)
