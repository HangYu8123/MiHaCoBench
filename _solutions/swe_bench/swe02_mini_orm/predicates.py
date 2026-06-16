"""predicates.py — predicate factories for the mini_orm query engine.

Provides three comparison predicates (eq, gt, lt) and a logical AND combinator.
Each predicate is a callable (dict -> bool).
"""
from __future__ import annotations

from typing import Any, Callable


def eq(field: str, value: Any) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] == value."""
    def _predicate(row: dict) -> bool:
        return row[field] == value
    return _predicate


def gt(field: str, value: Any) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] > value."""
    def _predicate(row: dict) -> bool:
        return row[field] > value
    return _predicate


def lt(field: str, value: Any) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] < value."""
    def _predicate(row: dict) -> bool:
        return row[field] < value
    return _predicate


def and_(*predicates: Callable[[dict], bool]) -> Callable[[dict], bool]:
    """Return a predicate that is True when ALL given predicates are True."""
    def _predicate(row: dict) -> bool:
        return all(p(row) for p in predicates)
    return _predicate
