# SWE-Bench 09 — `evolve_ttl_index`: range-invalidate without desyncing the index

**Created:** 2026-06-17 · **Category:** swe_bench · **Weight:** 6

Implement a small in-memory store with **TTL expiry**, **LRU eviction**, and a
**secondary field index**, then add a new **range-invalidation** operation. The
hard part is cross-module: the store and the index must stay consistent through
**every** removal path — and the new operation is easy to implement in a way that
silently desynchronises them.

Structure your solution as three modules:

```
index.py   — class FieldIndex: maps a field value -> the set of keys carrying it
store.py   — class Store:       primary key->record map; TTL + LRU; keeps the index consistent
db.py      — class DB:          the FACADE wiring a FieldIndex + a Store  (from db import DB)
```

## The consistency invariant (the crux)

At all times, **the set of keys referenced by the index must equal the set of live
keys in the store.** Whenever a key leaves the store — by overwrite, LRU eviction,
TTL expiry, explicit delete, **or range invalidation** — the index entry for that
key must be removed too. The reference design funnels all removals through one
private helper `Store._unlink(key)` that drops the key from the primary map *and*
calls `index.remove(...)`. Any removal that bypasses that helper leaves the index
pointing at keys that no longer exist.

## Public contract

### `index.py`

```python
class FieldIndex:
    def add(self, key, field_value) -> None: ...
    def remove(self, key, field_value) -> None: ...      # no-op if absent
    def keys_with(self, field_value) -> set: ...          # copy of the key set
    def all_indexed_keys(self) -> set: ...                # union over all field values
```

### `store.py`

```python
class Store:
    def __init__(self, capacity: int, index, clock) -> None: ...
        # capacity >= 1; `index` is a FieldIndex; `clock` is a zero-arg callable -> "now"
    def put(self, key, value, field_value, ttl=None) -> None: ...
        # insert/overwrite; expire_at = clock()+ttl when ttl is not None;
        # mark MRU; evict LRU while over capacity (all removals via _unlink)
    def get(self, key): ...                  # KeyError if absent or expired; marks MRU
    def delete(self, key) -> None: ...        # remove if present (via _unlink)
    def range_invalidate(self, lo, hi) -> None: ...
        # remove EVERY live entry whose field value is in the closed range [lo, hi]
    def live_keys(self) -> set: ...           # live (non-expired) keys
```

Expiry is **lazy**: a key whose `expire_at <= clock()` is treated as gone (and
unlinked) the next time the store is touched.

### `db.py` (facade)

```python
class DB:
    def __init__(self, capacity: int, clock=None) -> None: ...
        # clock defaults to time.monotonic; inject a callable for deterministic TTL
    def put(self, key, value, field_value, ttl=None) -> None: ...
    def get(self, key): ...
    def delete(self, key) -> None: ...
    def range_invalidate(self, lo, hi) -> None: ...
    def query_by_field(self, field_value) -> set: ...   # live keys with that field
    def index_is_consistent(self) -> bool: ...           # indexed keys == live keys
```

`from db import DB` must work. The grader imports `FieldIndex` from `index.py`,
`Store` from `store.py`, and `DB` from `db.py`.

## Required behaviour (worked examples)

```python
clock = FakeClock()                 # a zero-arg callable returning a controllable "now"
db = DB(capacity=8, clock=clock)

db.put("a", 1, field_value=10)
db.put("b", 2, field_value=10)
db.put("c", 3, field_value=20)
assert db.query_by_field(10) == {"a", "b"}

db.range_invalidate(5, 15)          # removes every key with field in [5, 15] -> a, b
import pytest
with pytest.raises(KeyError):
    db.get("a")
assert db.query_by_field(10) == set()      # <-- index must NOT keep ghost keys
assert db.query_by_field(20) == {"c"}
assert db.index_is_consistent()            # indexed keys == live keys
```

## Known bug description (for SWE-bench fault localisation)

The **observed symptom** is at the facade: after `db.range_invalidate(lo, hi)`,
`db.get(key)` on a removed key correctly raises `KeyError`, **but**
`db.query_by_field(field)` still returns the removed keys and
`db.index_is_consistent()` is `False`. All other operations — `put`, `get`,
overwrite, LRU eviction, TTL expiry, `delete` — keep the index consistent.

The **root cause** is in `store.py`: `range_invalidate` removes its victims
directly from the primary map instead of routing them through `_unlink`, so the
secondary index in `index.py` is never updated. **Your task:** make
`range_invalidate` remove each victim through the same single path the other
operations use, so the store/index invariant always holds.

## Constraints

- **stdlib only** — no third-party packages.
- Keys, values, and field values may be any hashable objects; field values used
  with `range_invalidate` are mutually comparable (e.g. integers).
- Determinism: inject `clock` for TTL tests; no real sleeping.
