# Harness 08 — `txnkv`: Transactional Key-Value Store with Savepoints and TTL

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 6

Implement a single-threaded, in-memory key-value store with a logical clock,
**stacked transactions**, **named savepoints** within the innermost transaction,
and **per-key TTL** (time-to-live). The difficulty is entirely in the
**interaction** of these features: buffered-write visibility across a transaction
stack, delete *tombstones* that must shadow lower layers and be undone correctly,
savepoints that survive a `rollback_to`, and TTL that is evaluated lazily against
the current clock (not at commit time). Getting any one interaction wrong
silently corrupts the visible state.

Keys and values are **strings**. Your solution must be **multi-file** (at least
two modules) and expose the public class through a module named `solution.py`
(e.g. `solution.py` may do `from store import Store`). The grader imports only
`Store` from `solution.py`; your internal module layout is yours to choose.

## Public contract

### class `Store`

Construct with no arguments: `store = Store()`. The store begins empty with the
logical clock at `0` and no active transaction.

A read always observes the **current visible state**: the committed store
overlaid by the active transaction stack (bottom frame → top frame), with TTL
expiry applied against the **current** `now()`.

#### Logical clock & TTL

| Method | Behavior |
|--------|----------|
| `now(self) -> int` | Current logical time. Starts at `0`. |
| `tick(self, dt: int) -> None` | Advance the clock by `dt`. `dt >= 0`, else `ValueError`. |

A key may carry an **expiry time** (an absolute logical time). Once
`now() >= expiry`, the key is considered **absent** (expired). Expiry is checked
**lazily on access** — nothing is eagerly purged. A `set` without a `ttl` clears
any prior expiry on that key.

#### Core operations

All core operations act on the current visible state (committed overlaid by the
transaction stack, with expiry applied).

| Method | Behavior |
|--------|----------|
| `set(self, key, value, ttl=None) -> None` | Set `key=value`. If `ttl` is not `None` it must be `> 0` (else `ValueError`) and the key expires at `now() + ttl`. If `ttl` is `None`, the key has **no expiry** and any previous expiry on the key is removed. |
| `get(self, key) -> str \| None` | Current visible value, or `None` if the key is absent or expired. |
| `delete(self, key) -> bool` | Remove `key`. Return `True` if the key was **present (and unexpired)** in the visible state immediately before this call, else `False`. |
| `keys(self, prefix="") -> list[str]` | **Sorted** list of all currently-present (unexpired) keys whose name starts with `prefix`. The default `prefix=""` matches every key. |

#### Transactions (a STACK; nesting allowed)

| Method | Behavior |
|--------|----------|
| `begin(self) -> None` | Push a new transaction frame. Subsequent writes are **buffered** in the top frame: visible to reads within the transaction stack, but not yet committed. |
| `commit(self) -> None` | Pop the top frame and **merge** its buffered writes into the frame below (or into the committed store if it was the outermost frame). `ValueError` if there is no active transaction. |
| `rollback(self) -> None` | Pop and **discard** the top frame's buffered writes (and any savepoints it holds). `ValueError` if there is no active transaction. |

#### Savepoints (within the **innermost** active transaction only)

| Method | Behavior |
|--------|----------|
| `savepoint(self, name) -> None` | Mark a named point in the **current innermost** transaction frame. `ValueError` if there is no active transaction. Re-using a `name` already set in the same frame **replaces** the old mark — its position moves to "now". |
| `rollback_to(self, name) -> None` | Undo all writes made in the innermost transaction **since `name` was set**, while **keeping the transaction open** and **keeping `name`** (and any savepoints set before it) valid. Savepoints set **after** `name` are discarded. `ValueError` if `name` is unknown in the current frame, or there is no active transaction. |
| `release(self, name) -> None` | Forget savepoint `name` (and any savepoints set **after** it) **without** undoing any writes. `ValueError` if `name` is unknown, or there is no active transaction. |

### Interaction semantics (specified exactly — implement these precisely)

1. **Buffered-write shadowing.** A write buffered in a frame shadows the values
   in lower frames and in the committed store, for reads made anywhere in the
   stack at or above that frame. The topmost frame that mentions a key wins.

2. **Delete tombstone.** A `delete` of a key that exists only in a lower frame or
   the committed store must, *within the current frame*, make the key read as
   **absent** (it leaves a tombstone — it does **not** reach down and erase the
   lower value). The tombstone is part of the frame's buffered state: it must be
   undone correctly by `rollback` and by `rollback_to` (i.e. after undoing past
   the point where the delete happened, the key reads with its lower/committed
   value again), and it merges down on `commit` (shadowing or deleting in the
   layer below).

3. **TTL inside a transaction.** A `ttl` given to `set` inside a transaction is
   part of that frame's buffered state. The expiry is an **absolute** time
   computed from `now()` at the moment of the `set`. On `commit` the buffered
   write (with its absolute expiry) merges down and is evaluated against `now()`
   **at access time**, *not* at commit time. On `rollback` / `rollback_to` it is
   discarded along with the rest of that scope's writes.

4. **Expiry on every read.** `get` and `keys(prefix)` always apply expiry against
   the **current** `now()`; a key whose `now() >= expiry` is absent everywhere it
   would otherwise be visible.

### Exception contract

| Condition | Raise |
|-----------|-------|
| `tick` with `dt < 0` | `ValueError` |
| `set` with `ttl is not None and ttl <= 0` | `ValueError` |
| `commit`, `rollback`, `savepoint`, `rollback_to`, or `release` with no active transaction | `ValueError` |
| `rollback_to(name)` / `release(name)` where `name` is not a savepoint in the current innermost frame | `ValueError` |

Assert exception **types**; messages are unspecified.

## Worked example

Each line shows a call and the resulting visible state / return value.

```text
s = Store()
s.now()                      -> 0
s.set("a", "1")              # committed: a=1
s.get("a")                   -> "1"

# --- buffered-write visibility + nested begin/commit merge ---
s.begin()                    # frame F1
s.set("a", "2")              # F1 buffers a=2 (shadows committed a=1)
s.get("a")                   -> "2"
s.begin()                    # frame F2 (innermost)
s.set("a", "3")
s.set("b", "x")
s.get("a")                   -> "3"      # F2 wins
s.commit()                   # merge F2 into F1: F1 now has a=3, b=x
s.get("a")                   -> "3"
s.get("b")                   -> "x"
s.rollback()                 # discard F1 entirely
s.get("a")                   -> "1"      # back to committed
s.get("b")                   -> None     # b was never committed

# --- savepoint + rollback_to keeps the txn open AND keeps the savepoint ---
s = Store()
s.set("k", "base")
s.begin()
s.set("k", "v1")
s.savepoint("sp")
s.set("k", "v2")
s.rollback_to("sp")          # undo back to sp (k=v1); txn still open
s.get("k")                   -> "v1"
s.set("k", "v3")
s.rollback_to("sp")          # sp is STILL valid and reusable -> k=v1 again
s.get("k")                   -> "v1"

# --- release: forget a savepoint without undoing ---
s.release("sp")              # sp forgotten; writes since sp are kept
s.get("k")                   -> "v1"
# a further rollback_to("sp") here would raise ValueError (sp is gone)

# --- delete tombstone undone by rollback_to ---
s = Store()
s.set("d", "present")        # committed
s.begin()
s.savepoint("sp")
s.delete("d")                -> True      # was present
s.get("d")                   -> None      # tombstone shadows committed
s.rollback_to("sp")          # tombstone undone
s.get("d")                   -> "present" # committed value visible again

# --- TTL expiry across tick ---
s = Store()
s.set("t", "v", ttl=5)       # now=0 -> expires at absolute time 5
s.get("t")                   -> "v"
s.tick(5)                    # now=5
s.get("t")                   -> None      # now() >= expiry
s.keys()                     -> []        # expired key is not listed
s.set("t", "v2")             # ttl=None clears any expiry
s.tick(100)
s.get("t")                   -> "v2"

# --- TTL set inside a txn merges, evaluated at access (not commit) ---
s = Store()
s.begin()
s.set("e", "v", ttl=3)       # now=0 -> absolute expiry 3
s.commit()
s.get("e")                   -> "v"       # alive at now=0
s.tick(3)
s.get("e")                   -> None      # expires by the clock, not at commit

# --- prefix scan ordering ---
s = Store()
for k in ["banana", "apple", "apricot", "cherry"]:
    s.set(k, "1")
s.keys("ap")                 -> ["apple", "apricot"]
s.keys()                     -> ["apple", "apricot", "banana", "cherry"]
```

## Notes

* The store is **single-threaded**; no concurrency is involved.
* Savepoints belong to the **innermost** frame only. A `begin` starts a fresh
  frame with no savepoints; `commit`/`rollback` of a frame takes its savepoints
  with it.
* Determinism: behavior is fully determined by the call sequence; no seeds.
* Your solution must be multi-file (≥2 modules) with the public `Store` exposed
  through `solution.py`.
