"""
predicates.py — predicate builders for the mini ORM.

Each factory returns a callable that accepts a single dict row and returns bool.
"""

from typing import Callable, Any


def eq(field: str, value: Any) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] == value."""
    def predicate(row: dict) -> bool:
        return row[field] == value
    return predicate


def gt(field: str, value: Any) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] > value."""
    def predicate(row: dict) -> bool:
        return row[field] > value
    return predicate


def lt(field: str, value: Any) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] < value."""
    def predicate(row: dict) -> bool:
        return row[field] < value
    return predicate


def and_(*preds: Callable) -> Callable[[dict], bool]:
    """Return a predicate that is True when ALL given predicates are True for a row."""
    def predicate(row: dict) -> bool:
        return all(p(row) for p in preds)
    return predicate
