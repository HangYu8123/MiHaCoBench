"""registry.py — Subscriber storage per event name."""

from typing import Callable


class Registry:
    """Holds per-event-name subscriber storage.

    Each entry tracks (priority, insertion_order, handler) so that handlers
    with equal priority are returned in subscription order (FIFO).
    """

    def __init__(self) -> None:
        # Maps event name -> list of [priority, insertion_order, handler]
        self._store: dict[str, list] = {}
        self._counter: int = 0

    def add(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Store handler for name at priority.

        Re-adding the same handler updates its priority while preserving
        its original insertion order (so tie-breaking remains stable).
        """
        if name not in self._store:
            self._store[name] = []

        entries = self._store[name]

        # Check if handler already registered
        for entry in entries:
            if entry[2] is handler:
                # Update priority in place; keep existing insertion_order
                entry[0] = priority
                return

        # New subscription
        self._counter += 1
        entries.append([priority, self._counter, handler])

    def remove(self, name: str, handler: Callable) -> None:
        """Remove handler from name. No-op if absent."""
        if name not in self._store:
            return
        entries = self._store[name]
        self._store[name] = [e for e in entries if e[2] is not handler]

    def handlers(self, name: str) -> list[tuple[int, Callable]]:
        """Return (priority, handler) pairs for name in descending priority order.

        Ties are broken by subscription order (earliest first).
        Returns an empty list if no handlers are registered.
        """
        if name not in self._store:
            return []

        # Sort by (-priority, insertion_order) so highest priority first,
        # ties in subscription (insertion) order.
        sorted_entries = sorted(
            self._store[name],
            key=lambda e: (-e[0], e[1]),
        )
        return [(e[0], e[2]) for e in sorted_entries]
