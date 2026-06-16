from cache import LRU, MISS


class KV:
    def __init__(self, backing, capacity: int) -> None:
        """Wrap a `Backing` instance with a fresh LRU cache of size `capacity`."""
        self._b = backing
        self._c = LRU(capacity)

    def get(self, key):
        """Return the value for `key`.

        - On a cache hit, return the cached value.
        - On a cache miss, read the backing store (which raises KeyError if the
          key is truly absent), populate the cache with the value, and return it.
        """
        result = self._c.get(key)
        if result is not MISS:
            return result
        # Cache miss — read from backing store (propagates KeyError if absent)
        value = self._b.get(key)
        self._c.put(key, value)
        return value

    def set(self, key, value) -> None:
        """Write-through: call `backing.set(key, value)` FIRST, then
        `cache.put(key, value)` so subsequent reads see the new value."""
        self._b.set(key, value)
        self._c.put(key, value)
