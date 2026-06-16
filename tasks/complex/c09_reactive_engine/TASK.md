# Complex 09 — `reactive_engine`: Reactive Dataflow Engine

**Created:** 2026-06-16 · **Category:** complex · **Weight:** 5

Implement a small **reactive dataflow engine**: a graph of named *cells* where a
cell is either a constant value or a formula computed from other cells. Reads are
**lazy and memoized**; whenever a cell's definition changes, that cell **and all
of its transitive dependents** must be invalidated so their next read recomputes
against the new inputs. Dependency cycles are rejected.

Spread the solution across **multiple files** — e.g. a `graph.py` that tracks the
dependency relationships and an `engine.py` that is the public **facade**. Use
**networkx** for the dependency graph (cycle detection, transitive-dependent
queries, topological ordering). The grader imports from `engine.py` only and does
not care about your internal module layout.

## Files to create

```
graph.py    — dependency tracking (a networkx DiGraph wrapper)
engine.py   — FACADE: defines the public `Engine` class
```

---

## Public contract (importable from `engine.py`)

### `class Engine`

Constructed with no arguments: `Engine()`.

| Method | Signature | Behaviour |
|---|---|---|
| `set_value` | `set_value(self, name, value) -> None` | Define/replace a **constant** cell holding `value`. Replacing a cell **invalidates the cached value of the cell AND all of its transitive dependents** (so their next `get()` recomputes). |
| `set_formula` | `set_formula(self, name, deps: list, fn) -> None` | Define/replace a **computed** cell whose value is `fn(*[get(d) for d in deps])`. Registers edges `dep -> name` in the dependency graph. Replacing an existing formula re-points its dependencies and invalidates its transitive dependents. Introducing a **cycle** MUST raise `ValueError` and leave the engine unchanged. |
| `get` | `get(self, name) -> value` | Return the cell's value, recomputing **lazily** from its dependencies when its cache is invalid and **memoizing** the result. A clean cache is returned **without** recomputation. Unknown `name` MUST raise `KeyError`. |
| `recompute_count` | `recompute_count(self, name) -> int` | How many times `name` has actually been **(re)computed** since its creation. A `get()` served from a clean cache does **not** increment this. Unknown `name` MUST raise `KeyError`. |
| `batch` | `batch(self, updates: dict) -> None` | Apply several `set_value` updates **atomically**: write every cell in `updates`, then ensure each affected cell recomputes **at most once** on the next reads (invalidation is **set-based**, not per-edge). Recomputation on the subsequent `get()` calls must respect the **topological order** of dependencies. |

---

## Semantics — exact rules

**Cells.** A name is either a *constant* cell (set by `set_value`) or a *computed*
cell (set by `set_formula`). `set_value` / `set_formula` may redefine a name and
may switch a name between constant and computed.

**Lazy + memoized reads.** `get(name)` returns the memoized value if the cell's
cache is clean. If the cache is dirty, `get` recomputes: for a formula cell it
evaluates `fn(get(d_1), …, get(d_k))` (recursing lazily into dependencies), caches
the result, and increments that cell's recompute count by exactly **one**. A
constant cell's value is always known and does not count as a recomputation.

**Transitive invalidation.** This is the heart of the task. When the definition
of a cell `x` changes (via `set_value`, `set_formula`, or `batch`), the cached
value of **every cell reachable from `x` along dependency edges** — i.e. the
*transitive dependents* of `x`, computed with `networkx.descendants` — becomes
stale and must recompute on its next read. It is **not** enough to invalidate
only the directly-adjacent dependents; staleness propagates all the way down the
chain (e.g. updating a leaf `a` must make a cell two hops away, `a -> b -> c`,
recompute and return the NEW value).

**Single recompute per invalidation.** After one invalidation, the first `get` of
an affected cell recomputes it once; subsequent `get`s (with no intervening
invalidation) are served from cache and do **not** bump `recompute_count`.

**Cycle detection & rollback.** `set_formula` that would introduce a cycle in the
dependency graph MUST raise `ValueError`. Both a **direct** cycle (`a` depends on
a chain that leads back to `a`) and an **indirect** multi-hop cycle must be
caught. On a rejected definition the engine must be **left exactly as it was**
(the failed `set_formula` has no side effects) and remain usable afterward.

**Unknown name.** `get` and `recompute_count` on a name that was never defined
raise `KeyError`.

---

## Notes

- Cell names may be any hashable Python value (`str`, `int`, …). Values may be any
  Python object; formulas are arbitrary pure callables.
- You may assume `deps` passed to `set_formula` are names that exist or will be
  defined; an edge to an as-yet-undefined name simply registers the dependency.
- Determinism: identical sequences of operations produce identical results.
- The grader imports `Engine` from `engine.py` only; internal module structure is
  irrelevant.
