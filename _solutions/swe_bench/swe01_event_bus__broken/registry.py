"""registry.py — Subscriber registry for the event bus.

Stores (handler, priority) pairs per event name.  Higher priority values mean
the handler is called earlier during publish.  Handlers with equal priority are
called in subscription order (stable sort).

NOTE: This is a BROKEN variant.  The ``remove`` method looks up the wrong key
(``name + "_unsub"`` instead of ``name``) so the removal is effectively a
no-op — an unsubscribed handler continues to receive published events.
Priority ordering and basic delivery remain correct.
"""
from __future__ import annotations

from typing import Any, Callable


class Registry:
    """Maps event names to an ordered list of (priority, handler) records."""

    def __init__(self) -> None:
        self._subs: dict[str, list[tuple[int, Callable]]] = {}

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #

    def add(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Register *handler* under *name* with the given *priority*."""
        bucket = self._subs.setdefault(name, [])
        for i, (pri, fn) in enumerate(bucket):
            if fn is handler:
                bucket[i] = (priority, handler)
                self._sort(bucket)
                return
        bucket.append((priority, handler))
        self._sort(bucket)

    def remove(self, name: str, handler: Callable) -> None:
        """Remove *handler* from *name*'s subscriber list.

        BUG: looks up the bucket under ``name + "_unsub"`` instead of ``name``,
        so the intended subscriber is never actually removed.
        """
        # PLANTED BUG: wrong key — should be ``name``, not ``name + "_unsub"``
        wrong_key = name + "_unsub"
        bucket = self._subs.get(wrong_key)
        if not bucket:
            return
        self._subs[wrong_key] = [(pri, fn) for (pri, fn) in bucket if fn is not handler]

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #

    def handlers(self, name: str) -> list[tuple[int, Callable]]:
        """Return the ordered handler list for *name* (highest priority first)."""
        return list(self._subs.get(name, []))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _sort(bucket: list[tuple[int, Callable]]) -> None:
        """Sort a bucket in-place: highest priority first, stable."""
        bucket.sort(key=lambda item: item[0], reverse=True)
