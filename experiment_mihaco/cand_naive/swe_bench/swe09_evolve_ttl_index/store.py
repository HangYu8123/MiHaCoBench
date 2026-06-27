"""Store: primary key->record map with TTL expiry, LRU eviction, and index consistency."""

from collections import OrderedDict


class Store:
    def __init__(self, capacity: int, index, clock) -> None:
        """
        capacity >= 1; `index` is a FieldIndex; `clock` is a zero-arg callable -> "now".
        """
        self._capacity = capacity
        self._index = index
        self._clock = clock
        # OrderedDict used as LRU: least-recently-used at front (oldest), MRU at back
        # Each entry: key -> (value, field_value, expire_at_or_None)
        self._data = OrderedDict()

    def _is_expired(self, key) -> bool:
        entry = self._data.get(key)
        if entry is None:
            return False
        _, _, expire_at = entry
        if expire_at is not None and expire_at <= self._clock():
            return True
        return False

    def _unlink(self, key) -> None:
        """Remove key from primary map AND remove from index. Central removal path."""
        entry = self._data.pop(key, None)
        if entry is not None:
            _, field_value, _ = entry
            self._index.remove(key, field_value)

    def _evict_expired(self) -> None:
        """Lazily evict all expired entries."""
        expired_keys = [k for k in list(self._data.keys()) if self._is_expired(k)]
        for k in expired_keys:
            self._unlink(k)

    def put(self, key, value, field_value, ttl=None) -> None:
        """
        Insert/overwrite. expire_at = clock()+ttl when ttl is not None.
        Mark MRU. Evict LRU while over capacity. All removals via _unlink.
        """
        # Evict expired first
        self._evict_expired()

        # If key already exists, unlink it first to clean up index for old field_value
        if key in self._data:
            self._unlink(key)

        expire_at = self._clock() + ttl if ttl is not None else None
        self._data[key] = (value, field_value, expire_at)
        # Mark as MRU by moving to end
        self._data.move_to_end(key)
        # Add to index
        self._index.add(key, field_value)

        # Evict LRU entries while over capacity
        while len(self._data) > self._capacity:
            # Oldest (LRU) is at the front
            lru_key = next(iter(self._data))
            self._unlink(lru_key)

    def get(self, key):
        """KeyError if absent or expired; marks MRU."""
        self._evict_expired()
        if key not in self._data:
            raise KeyError(key)
        if self._is_expired(key):
            self._unlink(key)
            raise KeyError(key)
        # Mark MRU
        self._data.move_to_end(key)
        value, _, _ = self._data[key]
        return value

    def delete(self, key) -> None:
        """Remove if present (via _unlink)."""
        self._evict_expired()
        if key in self._data:
            self._unlink(key)

    def range_invalidate(self, lo, hi) -> None:
        """
        Remove EVERY live entry whose field value is in the closed range [lo, hi].
        Routes all removals through _unlink to keep index consistent.
        """
        self._evict_expired()
        # Collect victims: keys whose field_value is in [lo, hi]
        victims = [
            k for k, (v, fv, ea) in list(self._data.items())
            if lo <= fv <= hi
        ]
        for k in victims:
            self._unlink(k)

    def live_keys(self) -> set:
        """Return the set of live (non-expired) keys."""
        self._evict_expired()
        return set(self._data.keys())
