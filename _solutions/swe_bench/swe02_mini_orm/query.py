"""query.py — immutable Query specification for the mini_orm query engine."""
from __future__ import annotations

from typing import Any, Callable

import predicates as _pred


class Query:
    """Immutable query specification: a list of predicates, sort keys, and a limit.

    Every mutating method returns a NEW Query; the original is unmodified.
    """

    def __init__(
        self,
        _predicates: tuple[Callable[[dict], bool], ...] = (),
        _order_by: tuple[tuple[str, bool], ...] = (),
        _limit: int | None = None,
    ) -> None:
        self._predicates = _predicates
        self._order_by = _order_by
        self._limit = _limit

    # ------------------------------------------------------------------
    # Builder methods — each returns a new Query
    # ------------------------------------------------------------------

    def where(self, field: str, op: str, value: Any) -> "Query":
        """Append a filter predicate.  op must be 'eq', 'gt', or 'lt'.

        Multiple .where() calls are ANDed together: a row must satisfy ALL
        conditions.
        """
        op = op.strip().lower()
        if op == "eq":
            p = _pred.eq(field, value)
        elif op == "gt":
            p = _pred.gt(field, value)
        elif op == "lt":
            p = _pred.lt(field, value)
        else:
            raise ValueError(f"Unknown operator: {op!r}.  Expected 'eq', 'gt', or 'lt'.")
        return Query(
            _predicates=self._predicates + (p,),
            _order_by=self._order_by,
            _limit=self._limit,
        )

    def order_by(self, field: str, descending: bool = False) -> "Query":
        """Append a sort key (last sort key wins on ties with earlier ones)."""
        return Query(
            _predicates=self._predicates,
            _order_by=self._order_by + ((field, descending),),
            _limit=self._limit,
        )

    def limit(self, n: int) -> "Query":
        """Cap the result at n rows."""
        return Query(
            _predicates=self._predicates,
            _order_by=self._order_by,
            _limit=n,
        )
