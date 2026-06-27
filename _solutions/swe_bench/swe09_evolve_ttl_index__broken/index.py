"""Secondary field index: maps a field value -> the set of keys carrying it.

The store is responsible for keeping this index consistent: every time a key
leaves the store (overwrite, eviction, TTL expiry, explicit delete, or range
invalidation) the store must call ``remove`` for that key. This module just
maintains the mapping; it never decides when a key is gone.
"""
from __future__ import annotations


class FieldIndex:
    def __init__(self) -> None:
        self._map: dict[object, set] = {}

    def add(self, key, field_value) -> None:
        """Associate ``key`` with ``field_value``."""
        self._map.setdefault(field_value, set()).add(key)

    def remove(self, key, field_value) -> None:
        """Drop the (key, field_value) association if present (no-op otherwise)."""
        bucket = self._map.get(field_value)
        if bucket is not None:
            bucket.discard(key)
            if not bucket:
                del self._map[field_value]

    def keys_with(self, field_value) -> set:
        """Return a copy of the set of keys currently associated with ``field_value``."""
        return set(self._map.get(field_value, ()))

    def all_indexed_keys(self) -> set:
        """Every key referenced anywhere in the index (for invariant checks)."""
        out: set = set()
        for bucket in self._map.values():
            out |= bucket
        return out
