"""Broken reference: TTL + LRU store whose ``range_invalidate`` leaves the index stale.

PLANTED DEFECT (cross-module invariant violation): ``range_invalidate`` removes its
victims by popping them directly from the primary map instead of funnelling through
``_unlink``. The primary store looks correct (a subsequent ``get`` raises KeyError),
but the secondary FieldIndex is never told, so ``query_by_field`` keeps returning the
removed (ghost) keys and the store/index invariant is broken. Every other removal
path (overwrite, eviction, TTL expiry, delete) still uses ``_unlink`` and behaves
correctly — only the newly added range invalidation regresses the invariant.
"""
from __future__ import annotations

from collections import OrderedDict


class Store:
    def __init__(self, capacity: int, index, clock) -> None:
        self.capacity = capacity
        self.index = index
        self.clock = clock
        self._data: "OrderedDict[object, tuple]" = OrderedDict()

    def _unlink(self, key) -> None:
        rec = self._data.pop(key, None)
        if rec is not None:
            _, field_value, _ = rec
            self.index.remove(key, field_value)

    def _expire(self) -> None:
        now = self.clock()
        dead = [k for k, (_, _, exp) in self._data.items() if exp is not None and exp <= now]
        for k in dead:
            self._unlink(k)

    def put(self, key, value, field_value, ttl=None) -> None:
        self._expire()
        if key in self._data:
            self._unlink(key)
        expire_at = (self.clock() + ttl) if ttl is not None else None
        self._data[key] = (value, field_value, expire_at)
        self._data.move_to_end(key)
        self.index.add(key, field_value)
        while len(self._data) > self.capacity:
            lru_key = next(iter(self._data))
            self._unlink(lru_key)

    def get(self, key):
        self._expire()
        if key not in self._data:
            raise KeyError(key)
        value, field_value, expire_at = self._data[key]
        self._data.move_to_end(key)
        return value

    def delete(self, key) -> None:
        self._expire()
        self._unlink(key)

    def range_invalidate(self, lo, hi) -> None:
        self._expire()
        victims = [k for k, (_, f, _) in self._data.items() if lo <= f <= hi]
        for k in victims:
            self._data.pop(k, None)  # BUG: bypasses _unlink -> index left stale

    def live_keys(self) -> set:
        self._expire()
        return set(self._data.keys())
