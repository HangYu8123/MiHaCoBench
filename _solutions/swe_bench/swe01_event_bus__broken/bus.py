"""bus.py — Public facade for the in-memory publish/subscribe event bus.

All public names are importable from this module only.  The underlying
``Event`` value type and the ``Registry`` storage layer live in separate
modules (``events.py``, ``registry.py``) so the architecture is
deliberately multi-file.

Public API
----------
Event          — immutable event value type (name + payload)
EventBus       — subscribe / unsubscribe / publish facade
"""
from __future__ import annotations

from typing import Any, Callable

from events import Event  # noqa: F401 – re-exported for callers
from registry import Registry

__all__ = ["Event", "EventBus"]


class EventBus:
    """In-memory publish/subscribe event bus.

    Handlers are callables that accept exactly one positional argument: the
    :class:`Event` being published.  Their return value is collected and
    included in the list returned by :meth:`publish`.
    """

    def __init__(self) -> None:
        self._registry = Registry()

    def subscribe(self, name: str, handler: Callable, priority: int = 0) -> None:
        """Register *handler* under event *name* with the given *priority*."""
        self._registry.add(name, handler, priority)

    def unsubscribe(self, name: str, handler: Callable) -> None:
        """Remove *handler* from event *name*'s subscriber list."""
        self._registry.remove(name, handler)

    def publish(self, event: Event) -> list:
        """Publish *event* and return a list of each handler's return value."""
        results: list[Any] = []
        for _priority, handler in self._registry.handlers(event.name):
            results.append(handler(event))
        return results
