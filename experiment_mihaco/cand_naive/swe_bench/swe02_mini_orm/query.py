"""
query.py — immutable Query specification class for the mini ORM.
"""

from typing import Optional, List, Tuple, Callable
from predicates import eq, gt, lt


class Query:
    """
    Immutable query specification. Each method returns a new Query instance.

    Multiple .where() calls are combined with AND — a row must satisfy ALL
    conditions to be included in the result.
    """

    def __init__(
        self,
        predicates: Optional[List[Callable]] = None,
        sort_fields: Optional[List[Tuple[str, bool]]] = None,
        limit_n: Optional[int] = None,
    ) -> None:
        # Use immutable tuples internally to emphasize immutability
        self._predicates: tuple = tuple(predicates) if predicates is not None else ()
        self._sort_fields: tuple = tuple(sort_fields) if sort_fields is not None else ()
        self._limit_n: Optional[int] = limit_n

    def where(self, field: str, op: str, value) -> "Query":
        """
        Return a new Query with an additional filter predicate appended.

        op must be one of: "eq", "gt", "lt".

        Multiple .where() calls are combined with AND — a row must satisfy
        ALL conditions to be included in the result.
        """
        op_map = {"eq": eq, "gt": gt, "lt": lt}
        if op not in op_map:
            raise ValueError(f"Unknown op '{op}'. Must be one of: eq, gt, lt")

        pred = op_map[op](field, value)
        # Correctly accumulate ALL predicates (fix: append, not replace)
        new_predicates = list(self._predicates) + [pred]

        return Query(
            predicates=new_predicates,
            sort_fields=list(self._sort_fields),
            limit_n=self._limit_n,
        )

    def order_by(self, field: str, descending: bool = False) -> "Query":
        """Return a new Query with a sort key appended (last wins)."""
        new_sort_fields = list(self._sort_fields) + [(field, descending)]
        return Query(
            predicates=list(self._predicates),
            sort_fields=new_sort_fields,
            limit_n=self._limit_n,
        )

    def limit(self, n: int) -> "Query":
        """Return a new Query that caps the result at n rows."""
        return Query(
            predicates=list(self._predicates),
            sort_fields=list(self._sort_fields),
            limit_n=n,
        )
