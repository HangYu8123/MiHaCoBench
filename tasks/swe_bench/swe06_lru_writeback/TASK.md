# SWE-Bench 06 — `lru_writeback`: Write-Through LRU Cache Over a Backing Store

**Created:** 2026-06-16 · **Category:** swe_bench · **Weight:** 6

Implement a write-through key/value store: a fast in-memory **LRU cache** sitting
in front of a slower **backing store**. Structure your solution as three modules:

```
store.py   — class Backing: the authoritative dict-backed key/value store
cache.py   — class LRU(capacity): a hand-rolled least-recently-used cache
kv.py      — class KV(backing, capacity): the FACADE wiring cache + backing
```

A user only ever interacts with `KV`. Reads should be served from the cache when
possible and fall through to the backing store on a miss; writes go *through* to
the backing store and the cache stays consistent.

---

## Files to create

```
store.py   — class Backing
cache.py   — class LRU
kv.py      — FACADE: class KV  (must allow `from kv import KV`)
```

---

## Public contract

### `store.py`

```python
class Backing:
    def __init__(self) -> None:
        """Create an empty dict-backed store."""

    def get(self, key):
        """Return the value stored under `key`, or raise KeyError if absent."""

    def set(self, key, value) -> None:
        """Insert or overwrite the value stored under `key`."""
```

### `cache.py`

A module-level sentinel and a hand-rolled LRU cache.

```python
MISS = object()   # module-level sentinel object

class LRU:
    def __init__(self, capacity: int) -> None:
        """Create a cache holding at most `capacity` entries (capacity >= 1)."""

    def get(self, key):
        """Return the cached value and mark `key` most-recently-used (MRU),
        or return the module-level `MISS` sentinel if `key` is not cached."""

    def put(self, key, value) -> None:
        """Insert OR update `key` with `value` and mark it MRU.

        - A NEW key is inserted; if the cache would exceed `capacity`, the
          LEAST-recently-used key is evicted.
        - An EXISTING key has its stored value OVERWRITTEN with `value` and is
          marked most-recently-used.
        """

    def invalidate(self, key) -> None:
        """Drop `key` from the cache if present (a no-op when absent)."""
```

`MISS` must be a sentinel distinct from any real value (in particular distinct
from `None`), so a legitimately cached `None` is never mistaken for a miss:
`cache.get(k) is MISS` is the only correct miss test.

### `kv.py` (facade)

```python
class KV:
    def __init__(self, backing, capacity: int) -> None:
        """Wrap a `Backing` instance with a fresh LRU cache of size `capacity`."""

    def get(self, key):
        """Return the value for `key`.

        - On a cache hit, return the cached value.
        - On a cache miss, read the backing store (which raises KeyError if the
          key is truly absent), populate the cache with the value, and return it.
        """

    def set(self, key, value) -> None:
        """Write-through: call `backing.set(key, value)` FIRST, then
        `cache.put(key, value)` so subsequent reads see the new value."""
```

`kv.py` must allow:

```python
from kv import KV
```

---

## Required behaviour (worked examples)

```python
backing = Backing()
kv = KV(backing, capacity=2)

kv.set("k", 1)
assert kv.get("k") == 1        # served from cache

kv.set("k", 2)                 # overwrite an EXISTING key (write-through)
assert kv.get("k") == 2        # must reflect the NEW value, not stale 1

# Read-through populates the cache from the backing store:
backing.set("only_in_backing", 99)
assert kv.get("only_in_backing") == 99

# A truly absent key surfaces KeyError through the facade:
import pytest
with pytest.raises(KeyError):
    kv.get("never_set")
```

---

## Known bug description (for SWE-bench fault localisation)

The **observed symptom** is at the facade: after overwriting an existing key
(`kv.set("k", 2)`), `kv.get("k")` keeps returning the *old* value. Single
writes of fresh keys, read-through from the backing store, `KeyError` on absent
keys, and LRU eviction all behave correctly.

The **root cause** lives in `cache.py`, not `kv.py`: `LRU.put`, when the key
already exists, only bumps its recency and returns early **without overwriting
the stored value**. The cache therefore serves the stale value forever.

**Your task:** make `LRU.put` overwrite the stored value for an existing key (and
still mark it most-recently-used), so that write-through stays consistent.

---

## Constraints

- Use **stdlib only** — no third-party packages.
- Keys and values may be any hashable / comparable Python objects.
- `MISS` must be a sentinel distinct from `None`.
- The grader imports `KV` from `kv.py`, and uses `Backing` from `store.py` and
  `LRU` / `MISS` from `cache.py`.
