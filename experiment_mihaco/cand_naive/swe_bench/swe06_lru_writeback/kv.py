import sys
import os

# Allow importing from the same directory
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from store import Backing  # noqa: F401 (re-exported for convenience)
from cache import LRU, MISS


class KV:
    def __init__(self, backing, capacity: int) -> None:
        """Wrap a `Backing` instance with a fresh LRU cache of size `capacity`."""
        self._backing = backing
        self._cache = LRU(capacity)

    def get(self, key):
        """Return the value for `key`.

        - On a cache hit, return the cached value.
        - On a cache miss, read the backing store (which raises KeyError if the
          key is truly absent), populate the cache with the value, and return it.
        """
        result = self._cache.get(key)
        if result is not MISS:
            return result
        # Cache miss: read from backing store (raises KeyError if absent)
        value = self._backing.get(key)
        self._cache.put(key, value)
        return value

    def set(self, key, value) -> None:
        """Write-through: call `backing.set(key, value)` FIRST, then
        `cache.put(key, value)` so subsequent reads see the new value."""
        self._backing.set(key, value)
        self._cache.put(key, value)
