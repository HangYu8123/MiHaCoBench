"""db.py — FACADE for mini_orm.

Re-exports Database and Query as the public API.
"""
from __future__ import annotations

from typing import Any

import predicates as _pred
from query import Query  # noqa: F401  (re-exported)


class Database:
    """In-memory "database" that wraps a list of dict rows."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def query(self) -> Query:
        """Return a fresh, empty Query bound to this Database."""
        return _BoundQuery(self)

    def run(self, q: "Query") -> list[dict]:
        """Execute query q against this Database's rows."""
        return _execute(self._rows, q)


def _execute(rows: list[dict], q: "Query") -> list[dict]:
    """Apply predicates, sorting, and limit from q to rows."""
    # 1. Apply ALL where() predicates (logical AND via and_combinator)
    if q._predicates:
        combined = _pred.and_(*q._predicates)
        result = [row for row in rows if combined(row)]
    else:
        result = list(rows)

    # 2. Apply order_by (stable sort; last key wins when multiple)
    for field, descending in q._order_by:
        result.sort(key=lambda r: r[field], reverse=descending)

    # 3. Apply limit
    if q._limit is not None:
        result = result[: q._limit]

    return result


# Make _BoundQuery a thin subclass so db.query() returns a Query
# that already knows which Database to use if users call .run() on it.
# However the spec says Database.run(q) is the execution point, so
# this is just a convenience.
class _BoundQuery(Query):
    """A Query that knows its parent Database (convenience only)."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db

    # Override builder methods to propagate _db (and keep immutability)
    def where(self, field: str, op: str, value: Any) -> "_BoundQuery":
        base = super().where(field, op, value)
        bq = _BoundQuery(self._db)
        bq._predicates = base._predicates
        bq._order_by = base._order_by
        bq._limit = base._limit
        return bq

    def order_by(self, field: str, descending: bool = False) -> "_BoundQuery":
        base = super().order_by(field, descending)
        bq = _BoundQuery(self._db)
        bq._predicates = base._predicates
        bq._order_by = base._order_by
        bq._limit = base._limit
        return bq

    def limit(self, n: int) -> "_BoundQuery":
        base = super().limit(n)
        bq = _BoundQuery(self._db)
        bq._predicates = base._predicates
        bq._order_by = base._order_by
        bq._limit = base._limit
        return bq

    def run(self) -> list[dict]:
        """Execute this query against the bound database."""
        return _execute(self._db._rows, self)


__all__ = ["Database", "Query"]
