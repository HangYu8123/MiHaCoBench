"""bus.py — Public facade: re-exports Event and provides EventBus."""

from typing import Callable

from events import Event
from registry import Registry

__all__ = ["Event", "EventBus"]


class EventBus:
    """In-memory publish/subscribe event bus.

    Each EventBus instance is independent; they do not share subscriber state.
    """

    def __init__(self) -> None:
        self._registry = Registry()

    def subscribe(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Register handler for events named name at the given priority.

        Re-subscribing the same handler updates its priority.
        """
        self._registry.add(name, handler, priority)

    def unsubscribe(self, name: str, handler: Callable) -> None:
        """Remove handler from name's subscriber list. No-op if not subscribed."""
        self._registry.remove(name, handler)

    def publish(self, event: Event) -> list:
        """Call every handler subscribed to event.name in descending priority order.

        Returns a list of each handler's return value, in call order.
        Returns an empty list if no handlers are subscribed.
        """
        pairs = self._registry.handlers(event.name)
        results = []
        for _priority, handler in pairs:
            results.append(handler(event))
        return results
