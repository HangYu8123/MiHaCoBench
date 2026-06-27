"""Database facade for the mini ORM query engine."""

from query import Query  # re-exported so `from db import Database, Query` works


class Database:
    """In-memory relational store over a list of dict rows."""

    def __init__(self, rows: list) -> None:
        """Store the list of dicts; no copying required."""
        self._rows = rows

    def query(self) -> Query:
        """Return a fresh, empty Query bound to this Database."""
        return Query(self)

    def run(self, q: Query) -> list:
        """
        Execute Query q against this Database's rows and return a new list
        of matching dicts.

        Execution order:
          1. Apply all .where() predicates (AND of all conditions).
          2. Apply .order_by() sort (stable; last field wins if multiple).
          3. Apply .limit() cap.

        Returned dicts are the original row objects (no deep copy needed).
        """
        # Step 1: filter — all() on empty tuple returns True, so no-filter case works
        rows = [r for r in self._rows if all(p(r) for p in q._predicates)]

        # Step 2: sort (stable sort, last order_by wins by design)
        if q._order is not None:
            rows = sorted(rows, key=lambda r: r[q._order], reverse=q._desc)

        # Step 3: limit — rows[:None] returns all rows; rows[:0] returns []
        rows = rows[:q._limit]

        return rows
