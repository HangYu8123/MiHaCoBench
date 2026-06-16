"""Deliberately-broken reference for debug/dbg03_lru_cache.

Planted defect (a freshness bug in the spirit of the c04 stale-value failure):
``get`` returns the value without refreshing the key's recency, so a key that was
just read can still be evicted as "least recently used". Eviction itself, value
updates, and the capacity invariant are correct, so the defect is localized to
read-recency — the grader must observe eviction *order* after a ``get``.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any


class RecentCache:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._data: OrderedDict[Any, Any] = OrderedDict()

    def get(self, key: Any) -> Any:
        if key not in self._data:
            return None
        return self._data[key]  # read does not refresh recency

    def put(self, key: Any, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)
