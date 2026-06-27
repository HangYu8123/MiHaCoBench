"""Predicate factory functions for the mini ORM query engine."""


def eq(field, value):
    """Return a predicate that is True when row[field] == value."""
    return lambda row, f=field, v=value: row[f] == v


def gt(field, value):
    """Return a predicate that is True when row[field] > value."""
    return lambda row, f=field, v=value: row[f] > v


def lt(field, value):
    """Return a predicate that is True when row[field] < value."""
    return lambda row, f=field, v=value: row[f] < v


def and_(*preds):
    """Return a predicate that is True when all given predicates are True."""
    return lambda row: all(p(row) for p in preds)
