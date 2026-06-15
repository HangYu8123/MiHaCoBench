"""Deliberately-broken reference for easy/e03_freq_lru.

Planted defects:
  1. Eviction policy is LFU (least-frequently-used) instead of LRU — wrong.
  2. histogram() includes evicted keys (freq dict is never cleaned up) — wrong.
Both defects are caught by the grader.
"""
from __future__ import annotations


class FreqLRU:
    """Broken FreqLRU: uses LFU eviction and leaks evicted keys into histogram."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self._capacity: int = capacity
        self._store: dict = {}
        # BUG: freq is never pruned on eviction
        self._freq: dict = {}

    def get(self, key) -> object:
        if key not in self._store:
            return None
        self._freq[key] = self._freq.get(key, 0) + 1
        return self._store[key]

    def put(self, key, value) -> None:
        if key in self._store:
            self._store[key] = value
            self._freq[key] = self._freq.get(key, 0) + 1
        else:
            if len(self._store) >= self._capacity:
                # BUG: evict least-FREQUENTLY-used, not least-recently-used
                evicted_key = min(self._store, key=lambda k: self._freq.get(k, 0))
                del self._store[evicted_key]
                # BUG: do NOT clean up self._freq[evicted_key] — leaks into histogram
            self._store[key] = value
            self._freq[key] = self._freq.get(key, 0) + 1

    def histogram(self) -> dict:
        # BUG: returns all freq entries, including evicted keys
        return dict(self._freq)

    def __len__(self) -> int:
        return len(self._store)
