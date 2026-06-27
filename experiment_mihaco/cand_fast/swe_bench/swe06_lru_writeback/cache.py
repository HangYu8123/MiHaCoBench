from collections import OrderedDict

MISS = object()  # module-level sentinel; use `is MISS` for miss detection


class LRU:
    def __init__(self, capacity: int) -> None:
        """Create a cache holding at most `capacity` entries (capacity >= 1)."""
        self._cap = capacity
        self._od = OrderedDict()

    def get(self, key):
        """Return the cached value and mark `key` most-recently-used (MRU),
        or return the module-level `MISS` sentinel if `key` is not cached."""
        if key not in self._od:
            return MISS
        self._od.move_to_end(key)
        return self._od[key]

    def put(self, key, value) -> None:
        """Insert OR update `key` with `value` and mark it MRU.

        - A NEW key is inserted; if the cache would exceed `capacity`, the
          LEAST-recently-used key is evicted.
        - An EXISTING key has its stored value OVERWRITTEN with `value` and is
          marked most-recently-used.
        """
        if key in self._od:
            self._od[key] = value          # overwrite stored value (the bug fix)
            self._od.move_to_end(key)      # mark MRU
            return
        self._od[key] = value
        if len(self._od) > self._cap:
            self._od.popitem(last=False)   # evict LRU (leftmost / oldest item)

    def invalidate(self, key) -> None:
        """Drop `key` from the cache if present (a no-op when absent)."""
        self._od.pop(key, None)
