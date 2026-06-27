"""DB: Facade wiring a FieldIndex + a Store."""

import time

from index import FieldIndex
from store import Store


class DB:
    def __init__(self, capacity: int, clock=None) -> None:
        """
        clock defaults to time.monotonic; inject a callable for deterministic TTL.
        """
        if clock is None:
            clock = time.monotonic
        self._index = FieldIndex()
        self._store = Store(capacity=capacity, index=self._index, clock=clock)

    def put(self, key, value, field_value, ttl=None) -> None:
        self._store.put(key, value, field_value, ttl=ttl)

    def get(self, key):
        return self._store.get(key)

    def delete(self, key) -> None:
        self._store.delete(key)

    def range_invalidate(self, lo, hi) -> None:
        self._store.range_invalidate(lo, hi)

    def query_by_field(self, field_value) -> set:
        """Return live keys with that field value."""
        # First trigger lazy expiry to keep index in sync
        self._store.live_keys()
        return self._index.keys_with(field_value)

    def index_is_consistent(self) -> bool:
        """Return True iff indexed keys == live keys."""
        live = self._store.live_keys()
        indexed = self._index.all_indexed_keys()
        return live == indexed
