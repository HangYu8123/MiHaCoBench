"""Gold reference for debug/dbg03_lru_cache — a recency-aware cache (stdlib only).

The original cache evicted correctly on overflow but treated reads as passive:
``get`` did not refresh a key's recency, so a freshly-read key could still be
chosen as the least-recently-used victim. The fix promotes a key to most-recently
-used on every successful ``get`` (and on ``put`` of an existing key).
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any


class RecentCache:
    """A fixed-capacity cache that evicts the least-recently-used entry.

    Both ``get`` (on a hit) and ``put`` count as *using* a key and refresh its
    recency. When a ``put`` grows the cache beyond ``capacity``, the
    least-recently-used entry is evicted.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._data: OrderedDict[Any, Any] = OrderedDict()

    def get(self, key: Any) -> Any:
        """Return the cached value for ``key`` (refreshing recency), or ``None``."""
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: Any, value: Any) -> None:
        """Insert/update ``key`` as the most-recently-used entry; evict if needed."""
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)
