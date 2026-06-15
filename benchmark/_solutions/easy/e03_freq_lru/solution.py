"""Gold reference for easy/e03_freq_lru — Frequency-tracking LRU Cache (stdlib only).

Eviction policy: Least-Recently-Used (recency only; frequency is tracked but
NOT used for eviction). Uses collections.OrderedDict as the ordered store.
"""
from __future__ import annotations

from collections import OrderedDict


class FreqLRU:
    """LRU cache that also tracks per-key access counts in a histogram.

    Parameters
    ----------
    capacity:
        Maximum number of distinct keys held simultaneously.  Must be >= 1;
        raises ValueError otherwise.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self._capacity: int = capacity
        # OrderedDict: key -> value  (LRU order: least-recently-used at front)
        self._store: OrderedDict = OrderedDict()
        # Parallel dict tracking access counts (get-hits + puts)
        self._freq: dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key) -> object:
        """Return the cached value for *key*, or None on a miss.

        A hit increments the key's access count and marks it most-recently-used.
        A miss returns None and changes no state.
        """
        if key not in self._store:
            return None
        # Move to end (most-recently-used position) and increment frequency.
        self._store.move_to_end(key)
        self._freq[key] += 1
        return self._store[key]

    def put(self, key, value) -> None:
        """Insert or update *key* with *value*, evicting the LRU key if needed.

        Both inserting a new key and updating an existing key count as one
        access (increment freq) and mark the key most-recently-used.
        If the cache is at capacity and *key* is new, the least-recently-used
        key is evicted before insertion.
        """
        if key in self._store:
            # Update existing key: refresh value, bump frequency, mark MRU.
            self._store[key] = value
            self._store.move_to_end(key)
            self._freq[key] += 1
        else:
            # New key: evict LRU if at capacity.
            if len(self._store) >= self._capacity:
                evicted_key, _ = self._store.popitem(last=False)
                del self._freq[evicted_key]
            self._store[key] = value
            self._freq[key] = 1

    def histogram(self) -> dict:
        """Return {key: access_count} for every key currently in the cache."""
        return dict(self._freq)

    def __len__(self) -> int:
        """Number of keys currently in the cache."""
        return len(self._store)
