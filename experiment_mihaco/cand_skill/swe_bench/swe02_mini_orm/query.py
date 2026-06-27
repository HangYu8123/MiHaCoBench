"""query.py — immutable Query specification for the mini ORM."""

from predicates import eq, gt, lt


_OP_MAP = {
    "eq": eq,
    "gt": gt,
    "lt": lt,
}


class Query:
    """Immutable query specification.

    Every method returns a *new* Query; the original is never mutated.
    """

    def __init__(self):
        # Internal state — not part of the public API.
        self._predicates: list = []   # accumulated filter predicates (AND semantics)
        self._order_field: str | None = None   # last order_by field (last wins)
        self._order_desc: bool = False
        self._limit: int | None = None

    # ------------------------------------------------------------------
    # Builder methods (each returns a new Query)
    # ------------------------------------------------------------------

    def where(self, field: str, op: str, value) -> "Query":
        """Return a new Query with an additional filter predicate appended.

        op must be one of: "eq", "gt", "lt".

        Multiple .where() calls are combined with AND — a row must satisfy
        ALL conditions to be included in the result.

        FIX: accumulate predicates via list concatenation so that every
        prior predicate is preserved in the new Query object.
        """
        factory = _OP_MAP[op]
        new_pred = factory(field, value)

        q = Query.__new__(Query)
        # KEY FIX: carry forward ALL accumulated predicates, then append the new one.
        q._predicates = self._predicates + [new_pred]
        q._order_field = self._order_field
        q._order_desc = self._order_desc
        q._limit = self._limit
        return q

    def order_by(self, field: str, descending: bool = False) -> "Query":
        """Return a new Query with the sort key set (last call wins)."""
        q = Query.__new__(Query)
        q._predicates = self._predicates   # same list reference is safe — we never mutate
        q._order_field = field             # last wins: overwrite, do NOT accumulate
        q._order_desc = descending
        q._limit = self._limit
        return q

    def limit(self, n: int) -> "Query":
        """Return a new Query that caps the result at n rows."""
        q = Query.__new__(Query)
        q._predicates = self._predicates
        q._order_field = self._order_field
        q._order_desc = self._order_desc
        q._limit = n
        return q
