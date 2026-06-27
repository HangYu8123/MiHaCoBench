from collections import OrderedDict

MISS = object()  # module-level sentinel object


class LRU:
    def __init__(self, capacity: int) -> None:
        """Create a cache holding at most `capacity` entries (capacity >= 1)."""
        self._capacity = capacity
        self._cache = OrderedDict()  # key -> value, ordered by recency (MRU at end)

    def get(self, key):
        """Return the cached value and mark `key` most-recently-used (MRU),
        or return the module-level `MISS` sentinel if `key` is not cached."""
        if key not in self._cache:
            return MISS
        # Move to end (MRU position)
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key, value) -> None:
        """Insert OR update `key` with `value` and mark it MRU.

        - A NEW key is inserted; if the cache would exceed `capacity`, the
          LEAST-recently-used key is evicted.
        - An EXISTING key has its stored value OVERWRITTEN with `value` and is
          marked most-recently-used.
        """
        if key in self._cache:
            # Overwrite the stored value and mark MRU
            self._cache[key] = value
            self._cache.move_to_end(key)
        else:
            # New key: insert and evict LRU if over capacity
            self._cache[key] = value
            self._cache.move_to_end(key)
            if len(self._cache) > self._capacity:
                # Remove the LRU item (first item in OrderedDict)
                self._cache.popitem(last=False)

    def invalidate(self, key) -> None:
        """Drop `key` from the cache if present (a no-op when absent)."""
        self._cache.pop(key, None)
