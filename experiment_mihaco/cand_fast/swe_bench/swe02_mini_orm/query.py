"""Immutable Query specification for the mini ORM query engine."""

import predicates as _predicates

_OP_MAP = {
    "eq": _predicates.eq,
    "gt": _predicates.gt,
    "lt": _predicates.lt,
}


class Query:
    """Immutable query specification. Each method returns a new Query."""

    def __init__(self, db, _predicates=(), _order=None, _desc=False, _limit=None):
        self._db = db
        self._predicates = _predicates  # tuple of callable(row) -> bool
        self._order = _order
        self._desc = _desc
        self._limit = _limit

    def where(self, field: str, op: str, value) -> "Query":
        """
        Return a new Query with an additional filter predicate appended.

        op must be one of: "eq", "gt", "lt".

        Multiple .where() calls are combined with AND — a row must satisfy
        ALL conditions to be included in the result.
        """
        factory = _OP_MAP[op]
        new_pred = factory(field, value)
        new_predicates = self._predicates + (new_pred,)
        return Query(self._db, new_predicates, self._order, self._desc, self._limit)

    def order_by(self, field: str, descending: bool = False) -> "Query":
        """Return a new Query with a sort key (last wins)."""
        return Query(self._db, self._predicates, field, descending, self._limit)

    def limit(self, n: int) -> "Query":
        """Return a new Query that caps the result at n rows."""
        return Query(self._db, self._predicates, self._order, self._desc, n)
