# SWE-Bench 02 — `mini_orm`: Tiny In-Memory Query Engine

**Created:** 2026-06-15 · **Category:** swe_bench · **Weight:** 6

Implement a tiny, in-memory relational query engine over a list of
`dict` rows. Structure your solution as multiple modules:

```
predicates.py   — predicate builders: eq, gt, lt, and an AND combinator
query.py        — class Query (immutable specification)
db.py           — class Database (facade re-exporting Database + Query)
```

---

## Files to create

```
predicates.py   — three predicate factories + an AND combinator
query.py        — class Query
db.py           — FACADE: re-exports Database and Query
```

---

## Public contract (every name must be importable from `db.py`)

### `predicates.py`

Three predicate factory functions and one combinator.  Each predicate
is a **callable** that accepts a single `dict` row and returns `bool`.

| Name | Signature | Behaviour |
|---|---|---|
| `eq(field, value)` | `eq(field: str, value) -> Callable[[dict], bool]` | Returns a predicate that is `True` when `row[field] == value`. |
| `gt(field, value)` | `gt(field: str, value) -> Callable[[dict], bool]` | Returns a predicate that is `True` when `row[field] > value`. |
| `lt(field, value)` | `lt(field: str, value) -> Callable[[dict], bool]` | Returns a predicate that is `True` when `row[field] < value`. |
| `and_(*predicates)` | `and_(*preds: Callable) -> Callable[[dict], bool]` | Returns a predicate that is `True` when **all** of the given predicates are `True` for that row. |

### `query.py`

```python
class Query:
    def where(self, field: str, op: str, value) -> "Query":
        """
        Return a new Query with an additional filter predicate appended.

        `op` must be one of: "eq", "gt", "lt".

        Multiple .where() calls are combined with AND — a row must satisfy
        ALL conditions to be included in the result.

        NOTE: a known bug exists where chaining two or more .where() calls
        may return rows that satisfy only ONE condition instead of ALL.
        The symptom is that .run() returns extra rows that should have been
        filtered out.
        """

    def order_by(self, field: str, descending: bool = False) -> "Query":
        """Return a new Query with a sort key appended (last wins)."""

    def limit(self, n: int) -> "Query":
        """Return a new Query that caps the result at n rows."""
```

`Query` is **immutable**: every method returns a *new* `Query` object;
the original is unmodified.

### `db.py` (facade)

```python
class Database:
    def __init__(self, rows: list[dict]) -> None:
        """Store the list of dicts; no copying required."""

    def query(self) -> Query:
        """Return a fresh, empty Query bound to this Database."""

    def run(self, q: Query) -> list[dict]:
        """
        Execute Query q against this Database's rows and return a new list
        of matching dicts.

        Execution order:
          1. Apply all .where() predicates (AND of all conditions).
          2. Apply .order_by() sort (stable; last field wins if multiple).
          3. Apply .limit() cap.

        Returned dicts are the original row objects (no deep copy needed).
        """
```

`db.py` must also re-export `Query` so the grader can do:
```python
from db import Database, Query
```

---

## Known bug description (for SWE-bench fault localisation)

When two or more `.where()` conditions are chained on the same `Query`,
the execution applies only the **last** predicate (ignoring all earlier
ones) instead of the logical AND of all predicates. As a result,
`.run()` returns rows that satisfy *only* the final `.where()` condition
rather than every condition. Single-filter queries, `.order_by()`, and
`.limit()` work correctly in the buggy version.

**Your task:** implement the correct behaviour so that chaining multiple
`.where()` calls applies ALL conditions simultaneously (logical AND).

---

## Constraints

- Use **stdlib only** — no third-party packages.
- Row dicts may contain values of any comparable type (int, float, str).
- `Query` objects must be **immutable** (chained calls return new objects).
- The grader imports `Database` and `Query` from `db.py` only.
