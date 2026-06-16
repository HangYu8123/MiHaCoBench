"""cache.py — a hand-rolled fixed-capacity LRU cache.

Recency is tracked by key-insertion order in an ``OrderedDict``-like dict
(Python 3.7+ dicts preserve insertion order). The most-recently-used key is
always the *last* one in iteration order; the least-recently-used key is the
*first*. ``put`` evicts the LRU key when the cache would exceed capacity.

``MISS`` is a module-level sentinel returned by :meth:`LRU.get` when the key is
not cached, so that a legitimately cached ``None`` value is never mistaken for a
miss.
"""
from __future__ import annotations

from typing import Any

# Module-level sentinel distinguishing "not cached" from a cached ``None``.
MISS = object()


class LRU:
    """A fixed-capacity least-recently-used cache."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._data: dict[Any, Any] = {}

    def _touch(self, key: Any) -> None:
        """Mark ``key`` as most-recently-used (move it to the end)."""
        value = self._data.pop(key)
        self._data[key] = value

    def get(self, key: Any) -> Any:
        """Return the cached value and mark it MRU, or ``MISS`` if not cached."""
        if key not in self._data:
            return MISS
        self._touch(key)
        return self._data[key]

    def put(self, key: Any, value: Any) -> None:
        """Insert or update ``key`` and mark it MRU, evicting the LRU if needed."""
        if key in self._data:
            # Existing key: overwrite the stored value AND mark most-recent.
            self._data.pop(key)
            self._data[key] = value
            return
        self._data[key] = value
        if len(self._data) > self._capacity:
            # Evict the least-recently-used key (first in insertion order).
            lru_key = next(iter(self._data))
            del self._data[lru_key]

    def invalidate(self, key: Any) -> None:
        """Drop ``key`` from the cache if present (no-op otherwise)."""
        self._data.pop(key, None)
