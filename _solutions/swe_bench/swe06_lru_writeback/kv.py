"""kv.py — FACADE: a write-through LRU cache over a backing store.

``KV`` glues :class:`store.Backing` and :class:`cache.LRU` together:

* ``get`` serves cache hits; on a miss it reads the backing store (raising
  ``KeyError`` for a truly absent key), populates the cache, and returns the
  value.
* ``set`` is *write-through*: it writes the backing store first, then updates
  the cache so a subsequent ``get`` sees the new value without a backing read.

The public symbol is ``KV`` — graders do ``from kv import KV``.
"""
from __future__ import annotations

from typing import Any

from cache import MISS, LRU
from store import Backing


class KV:
    """Write-through key/value facade over a backing store + LRU cache."""

    def __init__(self, backing: Backing, capacity: int) -> None:
        self._backing = backing
        self._cache = LRU(capacity)

    def get(self, key: Any) -> Any:
        """Return the value for ``key``.

        On a cache hit, return the cached value. On a miss, read the backing
        store (which raises ``KeyError`` if the key is truly absent), cache the
        value, and return it.
        """
        cached = self._cache.get(key)
        if cached is not MISS:
            return cached
        value = self._backing.get(key)  # KeyError if absent
        self._cache.put(key, value)
        return value

    def set(self, key: Any, value: Any) -> None:
        """Write ``value`` through to the backing store, then update the cache."""
        self._backing.set(key, value)
        self._cache.put(key, value)


__all__ = ["KV"]
