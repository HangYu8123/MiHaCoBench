"""registry.py — Per-event-name subscriber storage for the event bus."""

from __future__ import annotations

from typing import Callable


class Registry:
    """Holds subscriber lists keyed by event name.

    Each entry in the per-name list is a three-element list:
        [priority: int, insertion_index: int, handler: Callable]

    This lets us sort by (-priority, insertion_index) to get descending
    priority with stable subscription-order tie-breaking.
    """

    def __init__(self) -> None:
        # Maps event name -> list of [priority, insertion_index, handler]
        self._data: dict[str, list] = {}
        # Monotonically increasing counter to record subscription order
        self._counter: int = 0

    def add(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Store *handler* for *name* at *priority*.

        Re-adding the same handler (by equality, with identity as a fast path)
        updates its priority in-place rather than duplicating the entry.
        """
        entries = self._data.setdefault(name, [])
        for entry in entries:
            # Fast path: identity check; fall back to equality for bound methods
            if entry[2] is handler or entry[2] == handler:
                entry[0] = priority
                return
        entries.append([priority, self._counter, handler])
        self._counter += 1

    def remove(self, name: str, handler: Callable) -> None:
        """Remove *handler* from *name*'s subscriber list. No-op if absent."""
        if name not in self._data:
            return
        # Build a new list excluding the target handler.
        # Use equality (with identity short-circuit) to match add() semantics.
        self._data[name] = [
            e for e in self._data[name]
            if not (e[2] is handler or e[2] == handler)
        ]

    def handlers(self, name: str) -> list[tuple[int, Callable]]:
        """Return (priority, handler) pairs for *name* in descending priority order.

        Handlers with equal priority are returned in subscription order.
        Returns an empty list if no handlers are registered for *name*.
        The returned list is a snapshot — mutations during iteration are safe.
        """
        entries = self._data.get(name)
        if not entries:
            return []
        # Sort descending priority, then ascending insertion index for ties.
        sorted_entries = sorted(entries, key=lambda e: (-e[0], e[1]))
        return [(e[0], e[2]) for e in sorted_entries]
