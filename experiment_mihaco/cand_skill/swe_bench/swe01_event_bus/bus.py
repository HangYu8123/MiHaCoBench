"""Public facade for the in-memory publish/subscribe event bus.

Exports:
    Event    — immutable event value type (re-exported from events.py)
    EventBus — subscribe / unsubscribe / publish facade backed by Registry
"""

from __future__ import annotations

from typing import Callable

from events import Event
from registry import Registry

__all__ = ["Event", "EventBus"]


class EventBus:
    """In-memory publish/subscribe event bus.

    Each EventBus instance is fully independent — subscribing or unsubscribing
    on one bus has no effect on another.
    """

    def __init__(self) -> None:
        self._registry = Registry()

    def subscribe(
        self, name: str, handler: Callable, priority: int = 0
    ) -> None:
        """Register *handler* for events named *name* at *priority*.

        Re-subscribing the same handler object updates its priority.
        """
        self._registry.add(name, handler, priority)

    def unsubscribe(self, name: str, handler: Callable) -> None:
        """Remove *handler* from *name*'s subscriber list.

        No-op if *handler* is not currently subscribed to *name*.
        """
        self._registry.remove(name, handler)

    def publish(self, event: Event) -> list:
        """Call every handler subscribed to ``event.name`` in descending
        priority order (highest first; ties broken by subscription order).

        Returns a list of each handler's return value in call order.
        Returns an empty list if no handlers are subscribed for ``event.name``.
        """
        pairs = self._registry.handlers(event.name)
        return [handler(event) for _priority, handler in pairs]
