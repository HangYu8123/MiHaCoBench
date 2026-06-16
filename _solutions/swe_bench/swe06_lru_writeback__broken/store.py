"""store.py — the slow backing store sitting behind the LRU cache.

A trivial dict-backed key/value store. ``get`` raises ``KeyError`` for an
absent key (just like a real ``dict``); ``set`` inserts or overwrites.
"""
from __future__ import annotations

from typing import Any


class Backing:
    """A dict-backed key/value store (the authoritative source of truth)."""

    def __init__(self) -> None:
        self._data: dict[Any, Any] = {}

    def get(self, key: Any) -> Any:
        """Return the stored value for ``key`` or raise ``KeyError`` if absent."""
        return self._data[key]

    def set(self, key: Any, value: Any) -> None:
        """Insert or overwrite the value stored under ``key``."""
        self._data[key] = value
