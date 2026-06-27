"""predicates.py — predicate builders for the mini ORM."""

from typing import Callable


def eq(field: str, value) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] == value."""
    return lambda row: row[field] == value


def gt(field: str, value) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] > value."""
    return lambda row: row[field] > value


def lt(field: str, value) -> Callable[[dict], bool]:
    """Return a predicate that is True when row[field] < value."""
    return lambda row: row[field] < value


def and_(*preds: Callable) -> Callable[[dict], bool]:
    """Return a predicate that is True when ALL given predicates are True.

    - and_() with zero arguments returns a predicate that always returns True
      (vacuous truth — identity of logical AND).
    - Short-circuits on the first False (via all()).
    """
    return lambda row: all(p(row) for p in preds)
