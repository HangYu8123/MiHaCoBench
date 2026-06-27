"""Registry — per-event-name subscriber storage.

Each Registry instance maintains its own independent mapping of event names
to their subscribers.  This is the backing store for EventBus.

Storage format for each event name:
    [(insertion_seq, priority, handler), ...]

  - insertion_seq: monotonically increasing int used as tie-breaker so that
    handlers with equal priority are returned in subscription order.
  - priority: int (higher = called first).
  - handler: the callable registered by the caller.

Comparison rules:
  - Handler identity is always checked with ``is`` / ``is not`` to avoid
    false-positives with callables that accidentally compare equal.
"""

from __future__ import annotations

from typing import Callable


class Registry:
    """Subscriber storage for one event bus.

    Registry() takes no required constructor arguments.
    Multiple Registry instances are fully independent.
    """

    def __init__(self) -> None:
        # Per-instance dict: event_name -> list of (insertion_seq, priority, handler)
        # IMPORTANT: must be instance-level, not class-level, to keep
        # separate Registry / EventBus instances isolated.
        self._store: dict[str, list[tuple[int, int, Callable]]] = {}
        self._seq: int = 0  # global insertion counter across all event names

    def add(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Store *handler* for *name* at *priority*.

        Re-adding the same handler (by identity) updates its priority and
        refreshes its insertion sequence so ordering is stable on re-subscribe.
        Does NOT create a second entry.
        """
        entries = self._store.setdefault(name, [])

        # Check whether this exact handler object is already registered.
        for i, (seq, _p, h) in enumerate(entries):
            if h is handler:
                # Update priority in place; keep the original insertion_seq so
                # that same-priority ordering reflects the first subscription.
                entries[i] = (seq, priority, handler)
                return

        # New subscription — assign the next insertion sequence number.
        self._store[name].append((self._seq, priority, handler))
        self._seq += 1

    def remove(self, name: str, handler: Callable) -> None:
        """Remove *handler* from *name*'s subscriber list.

        No-op if *handler* is not subscribed or *name* is unknown.
        Uses identity comparison (``is``) so that functionally equal but
        distinct objects are not accidentally removed.
        """
        if name not in self._store:
            return
        self._store[name] = [
            (seq, p, h)
            for seq, p, h in self._store[name]
            if h is not handler
        ]

    def handlers(self, name: str) -> list[tuple[int, Callable]]:
        """Return ``(priority, handler)`` pairs for *name* in descending
        priority order (highest first).

        Ties in priority are broken by subscription order (earliest first),
        thanks to the stable Timsort used by Python's ``sorted``.

        Returns an empty list if *name* has no subscribers.
        """
        entries = self._store.get(name, [])
        if not entries:
            return []

        # Sort descending by priority; for equal priorities Timsort keeps
        # the original relative order (insertion order), satisfying the
        # "same priority → subscription order" guarantee.
        sorted_entries = sorted(entries, key=lambda x: (-x[1], x[0]))

        return [(p, h) for _seq, p, h in sorted_entries]
