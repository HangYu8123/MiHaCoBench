# Debug 03 — `lru_cache`: a hot key gets evicted

**Created:** 2026-06-15 · **Category:** debug · **Weight:** 2

You are given a **buggy** least-recently-used cache. Find and fix the defect,
then write your corrected solution as `solution.py` (**standard library only**).
Keep the public contract below exactly; do not rename the class or its methods.

## Buggy implementation

```python
from collections import OrderedDict


class RecentCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key):
        if key not in self._data:
            return None
        return self._data[key]

    def put(self, key, value):
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)
```

## Symptom (failing behavior)

A `get` is supposed to count as *using* a key and make it most-recently-used, so
a just-read key should survive the next eviction. Instead, reads are ignored for
recency and a freshly-read key can be evicted:

```text
c = RecentCache(2)
c.put("a", 1); c.put("b", 2)
c.get("a")          # read "a" — it should now be most-recently-used
c.put("c", 3)       # capacity exceeded → should evict "b"
c.get("a")          # actual: None  (wrong — "a" was evicted)
                    # expected: 1    ("b" should have been the victim)
```

Eviction on overflow, value updates, and the capacity bound are already correct —
only read-recency is broken.

## Public contract (must match exactly)

```python
class RecentCache:
    def __init__(self, capacity: int) -> None: ...      # capacity <= 0 → ValueError
    def get(self, key) -> object | None: ...            # value, or None if absent
    def put(self, key, value) -> None: ...
```

* Capacity-bounded: a `put` that grows the cache beyond `capacity` evicts the
  **least-recently-used** entry.
* Both a successful `get` **and** a `put` count as using a key and make it the
  **most-recently-used** entry.
* `get` on an absent key returns `None` and changes nothing.

## Notes

* Standard library only (`collections.OrderedDict` is a convenient basis).
* Determinism: identical operation sequence ⇒ identical behavior.
