"""Gold reference: TTL + LRU store that keeps a secondary FieldIndex consistent.

The class invariant is: the set of keys referenced by the index equals the set of
live keys in the store. Every removal therefore funnels through the single private
helper ``_unlink``, which drops the key from the primary map AND notifies the
index. ``range_invalidate`` (the feature this task adds) is no exception — it must
remove its victims via ``_unlink`` so the index never goes stale.
"""
from __future__ import annotations

from collections import OrderedDict


class Store:
    def __init__(self, capacity: int, index, clock) -> None:
        self.capacity = capacity
        self.index = index
        self.clock = clock
        # key -> (value, field_value, expire_at_or_None)
        self._data: "OrderedDict[object, tuple]" = OrderedDict()

    # -- the single removal path ------------------------------------------------
    def _unlink(self, key) -> None:
        """Remove ``key`` from the primary map AND keep the index consistent."""
        rec = self._data.pop(key, None)
        if rec is not None:
            _, field_value, _ = rec
            self.index.remove(key, field_value)

    def _expire(self) -> None:
        now = self.clock()
        dead = [k for k, (_, _, exp) in self._data.items() if exp is not None and exp <= now]
        for k in dead:
            self._unlink(k)

    # -- public operations ------------------------------------------------------
    def put(self, key, value, field_value, ttl=None) -> None:
        self._expire()
        if key in self._data:
            self._unlink(key)  # remove the old record (and its old index entry)
        expire_at = (self.clock() + ttl) if ttl is not None else None
        self._data[key] = (value, field_value, expire_at)
        self._data.move_to_end(key)
        self.index.add(key, field_value)
        while len(self._data) > self.capacity:
            lru_key = next(iter(self._data))
            self._unlink(lru_key)  # eviction also goes through the single path

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
        """Remove every live entry whose field value is in the closed range [lo, hi]."""
        self._expire()
        victims = [k for k, (_, f, _) in self._data.items() if lo <= f <= hi]
        for k in victims:
            self._unlink(k)  # MUST funnel through _unlink to keep the index consistent

    def live_keys(self) -> set:
        self._expire()
        return set(self._data.keys())
