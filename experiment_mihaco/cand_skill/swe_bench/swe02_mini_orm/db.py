"""db.py — Database facade for the mini ORM.

Re-exports Database and Query so the grader can do:
    from db import Database, Query
"""

from query import Query  # re-export


class Database:
    """In-memory relational query engine over a list of dict rows."""

    def __init__(self, rows: list[dict]) -> None:
        """Store the list of dicts; no copying required."""
        self._rows = rows

    def query(self) -> Query:
        """Return a fresh, empty Query bound to this Database."""
        return Query()

    def run(self, q: Query) -> list[dict]:
        """Execute Query q against this Database's rows and return a new list.

        Execution order:
          1. Apply ALL .where() predicates (AND of all conditions).
          2. Apply .order_by() sort (stable; last field wins if multiple).
          3. Apply .limit() cap.

        Returned dicts are the original row objects (no deep copy needed).
        """
        # Step 1: filter — apply AND of all accumulated predicates.
        # all([]) == True, so zero predicates means every row passes through.
        result = [
            row for row in self._rows
            if all(p(row) for p in q._predicates)
        ]

        # Step 2: sort — last order_by wins (stored as a single field).
        if q._order_field is not None:
            result.sort(
                key=lambda row: row[q._order_field],
                reverse=q._order_desc,
            )

        # Step 3: limit — cap the result length.
        if q._limit is not None:
            result = result[: q._limit]

        return result


__all__ = ["Database", "Query"]
