"""registry.py — Subscriber registry for the event bus.

Stores (handler, priority) pairs per event name.  Higher priority values mean
the handler is called earlier during publish.  Handlers with equal priority are
called in subscription order (stable sort).
"""
from __future__ import annotations

from typing import Any, Callable


class Registry:
    """Maps event names to an ordered list of (priority, handler) records.

    Internal representation:
        _subs: dict[str, list[tuple[int, Callable]]]

    The list for each name is kept sorted descending by priority so that
    publish() can iterate straight through it.
    """

    def __init__(self) -> None:
        # { event_name -> [(priority, handler), ...] }  — sorted high->low
        self._subs: dict[str, list[tuple[int, Callable]]] = {}

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #

    def add(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Register *handler* under *name* with the given *priority*.

        If the exact same handler object is already registered for *name*, the
        existing record is updated in-place (priority may change).
        """
        bucket = self._subs.setdefault(name, [])
        # Check for existing registration by identity
        for i, (pri, fn) in enumerate(bucket):
            if fn is handler:
                # Update priority in place
                bucket[i] = (priority, handler)
                self._sort(bucket)
                return
        bucket.append((priority, handler))
        self._sort(bucket)

    def remove(self, name: str, handler: Callable) -> None:
        """Remove *handler* from *name*'s subscriber list (no-op if absent)."""
        bucket = self._subs.get(name)
        if not bucket:
            return
        # Match by identity (is), not equality (==)
        self._subs[name] = [(pri, fn) for (pri, fn) in bucket if fn is not handler]

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #

    def handlers(self, name: str) -> list[tuple[int, Callable]]:
        """Return the ordered handler list for *name* (highest priority first).

        Returns an empty list if no subscribers exist for *name*.
        """
        return list(self._subs.get(name, []))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _sort(bucket: list[tuple[int, Callable]]) -> None:
        """Sort a bucket in-place: highest priority first, stable."""
        bucket.sort(key=lambda item: item[0], reverse=True)
