from cache import LRU, MISS


class KV:
    """Write-through key/value facade: LRU cache in front of a Backing store."""

    def __init__(self, backing, capacity: int) -> None:
        """Wrap a `Backing` instance with a fresh LRU cache of size `capacity`."""
        self._backing = backing
        self._cache = LRU(capacity)

    def get(self, key):
        """Return the value for `key`.

        - On a cache hit, return the cached value.
        - On a cache miss, read the backing store (raises KeyError if absent),
          populate the cache, and return the value.
        """
        cached = self._cache.get(key)
        if cached is not MISS:
            return cached

        # Cache miss: read from backing (let KeyError propagate if absent).
        value = self._backing.get(key)
        self._cache.put(key, value)
        return value

    def set(self, key, value) -> None:
        """Write-through: update the backing store first, then the cache."""
        self._backing.set(key, value)   # durable write first
        self._cache.put(key, value)     # keep cache consistent
