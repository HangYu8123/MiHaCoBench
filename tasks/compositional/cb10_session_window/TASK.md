# Compositional 10 — `session_window`: sessionize events with an inclusive gap boundary

**Created:** 2026-06-17 · **Category:** compositional · **Weight:** 4

Group time-ordered events into **sessions**. The difficulty is entirely in the
**boundary semantics**: the maximum gap is **inclusive**, so two consecutive
events whose timestamps differ by **exactly** `gap` stay in the *same* session;
only a gap **strictly greater than** `gap` starts a new one. Getting `>` vs `>=`
wrong merges or splits sessions at every exact-gap boundary.

Implement your solution in a single file `solution.py`. It composes **pandas**
(the table + total ordering) and **numpy** (consecutive gaps).

## Public contract

### `sessionize(df: pandas.DataFrame, gap: float) -> list[dict]`

**Ordering (total order).** Events are processed in `(df["ts"] ASC, df["id"] ASC)`
order. `"id"` is a unique integer column used as the **stable tie-breaker** so
two events with the same `ts` have a deterministic order. `"ts"` is a numeric
timestamp column. Rows of `df` may arrive in any order; you must sort them.

**Session rule.** Walking events in that order, the gap between an event and the
**immediately preceding** event is `ts[i] - ts[i-1]`. If that gap is `<= gap`, the
event **continues** the current session; if it is **strictly greater than** `gap`,
the event **starts a new** session. (The first event always starts the first
session.)

**Return value.** A list of session dicts, **in start order**, each with
**exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `ids` | `list[int]` | the session's event ids, in `(ts, id)` order |
| `start_ts` | (ts dtype) | timestamp of the session's first event |
| `end_ts` | (ts dtype) | timestamp of the session's last event |
| `count` | `int` | number of events in the session (`len(ids)`) |

Every event belongs to **exactly one** session; sessions are non-empty and never
overlap; the union of all `ids` is every id in `df`.

### Exception contract

| Condition | Raise |
|-----------|-------|
| `gap < 0` | `ValueError` |
| the `"id"` column is missing | `KeyError` |
| the `"ts"` column is missing | `KeyError` |

`df` with **zero rows** returns `[]` (not an error). Assert exception **types**;
messages are unspecified.

## Worked example

Events already shown in `(ts, id)` order, with `gap = 5`:

```
ts=0  id=1
ts=5  id=2     gap from prev = 5   (== gap -> SAME session)
ts=10 id=3     gap = 5             (== gap -> SAME session)
ts=20 id=4     gap = 10            (>  gap -> NEW session)
```

Result:

```python
[
  {"ids": [1, 2, 3], "start_ts": 0,  "end_ts": 10, "count": 3},
  {"ids": [4],       "start_ts": 20, "end_ts": 20, "count": 1},
]
```

A solution that breaks on `>= gap` would instead split the first three events into
separate sessions — the exact-gap boundary is where it goes wrong.

## Notes

* `pandas` and `numpy` must both appear in your source and be used (surface-form check).
* The function is **pure**: it must not mutate `df`.
* Determinism: the order is fully determined by `(ts, id)`; no seeds needed.
