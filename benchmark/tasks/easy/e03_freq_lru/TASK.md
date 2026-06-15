# Easy 03 — `freq_lru`: Frequency-tracking LRU Cache

**Created:** 2026-06-15 · **Category:** easy · **Weight:** 1

Implement a Least-Recently-Used cache that also tracks per-key access counts.
Write your solution as `solution.py`. Use the **standard library only**.

## Public contract (must match exactly)

```python
class FreqLRU:
    def __init__(self, capacity: int) -> None: ...
    def get(self, key) -> object: ...
    def put(self, key, value) -> None: ...
    def histogram(self) -> dict: ...
    def __len__(self) -> int: ...
```

### `__init__(self, capacity: int)`

Create a cache that holds at most `capacity` distinct keys.
Raise `ValueError` if `capacity <= 0`.

### `get(self, key) -> value or None`

Return the value associated with `key` if it is currently in the cache.
A **hit** (key present): increments that key's access count by 1 and marks
the key as **most-recently-used**. Returns the stored value.
A **miss** (key absent): returns `None` and counts nothing — no state change.

### `put(self, key, value) -> None`

Insert or update a key-value pair.

* If `key` is **already in the cache**: update its value, increment its access
  count by 1, and mark it most-recently-used. No eviction.
* If `key` is **new** and `len(cache) < capacity`: insert the key, set its
  access count to 1, mark it most-recently-used.
* If `key` is **new** and `len(cache) == capacity`: **evict** the
  least-recently-used key (the one that was accessed (get-hit or put) least
  recently among all current residents), then insert the new key with access
  count 1 as most-recently-used.

Eviction is based **solely on recency of use** — not on access count.

### `histogram(self) -> dict`

Return a `dict` mapping each key **currently in the cache** to its integer
access count. Keys that have been evicted must NOT appear. Order does not
matter.

### `__len__(self) -> int`

Return the number of keys currently in the cache (0 ≤ len ≤ capacity).

## Semantics summary

| operation | increments freq? | updates recency? |
|---|---|---|
| `get` hit | yes (+1) | yes (MRU) |
| `get` miss | no | no |
| `put` (existing key) | yes (+1) | yes (MRU) |
| `put` (new key) | sets to 1 | yes (MRU) |

Eviction policy: **LRU** — the key that was used (get-hit or put) least
recently is evicted first.

## Notes

* All keys and values may be any hashable Python objects.
* `histogram()` reflects only the *currently resident* keys; after eviction
  the evicted key's count disappears.
* Determinism: given the same sequence of operations the cache state and
  histogram are always identical.
