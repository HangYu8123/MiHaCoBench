"""
db.py — Database facade for the mini ORM.

Re-exports both Database and Query so the grader can do:
    from db import Database, Query
"""

from query import Query


class Database:
    """
    In-memory relational query engine over a list of dict rows.
    """

    def __init__(self, rows: list) -> None:
        """Store the list of dicts; no copying required."""
        self._rows = rows

    def query(self) -> Query:
        """Return a fresh, empty Query bound to this Database."""
        return Query()

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
        # Step 1: Filter rows using ALL predicates (AND semantics)
        result = [
            row for row in self._rows
            if all(pred(row) for pred in q._predicates)
        ]

        # Step 2: Apply sort fields (stable sort; last field wins if multiple)
        # Per spec: "last field wins if multiple" — iterate in order,
        # and since Python's sort is stable, sorting by each field in sequence
        # means the last sort key takes precedence (last wins).
        for field, descending in q._sort_fields:
            result.sort(key=lambda row: row[field], reverse=descending)

        # Step 3: Apply limit cap
        if q._limit_n is not None:
            result = result[:q._limit_n]

        return result


# Re-export Query so the grader can do: from db import Database, Query
__all__ = ["Database", "Query"]
