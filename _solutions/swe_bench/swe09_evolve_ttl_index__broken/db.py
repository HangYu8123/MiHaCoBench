"""Facade wiring a FieldIndex and a Store together. Users interact only with DB.

``from db import DB`` must work. A clock callable can be injected for
deterministic TTL testing; it defaults to ``time.monotonic``.
"""
from __future__ import annotations

import time

from index import FieldIndex
from store import Store


class DB:
    def __init__(self, capacity: int, clock=None) -> None:
        self.index = FieldIndex()
        self.clock = clock if clock is not None else time.monotonic
        self.store = Store(capacity, self.index, self.clock)

    def put(self, key, value, field_value, ttl=None) -> None:
        self.store.put(key, value, field_value, ttl=ttl)

    def get(self, key):
        return self.store.get(key)

    def delete(self, key) -> None:
        self.store.delete(key)

    def range_invalidate(self, lo, hi) -> None:
        self.store.range_invalidate(lo, hi)

    def query_by_field(self, field_value) -> set:
        """Live keys currently associated with ``field_value`` (index-backed)."""
        self.store._expire()
        return self.index.keys_with(field_value)

    def index_is_consistent(self) -> bool:
        """Class invariant: indexed keys == live keys in the store."""
        return self.index.all_indexed_keys() == self.store.live_keys()
