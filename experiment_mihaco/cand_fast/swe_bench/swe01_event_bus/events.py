"""events.py — Immutable Event value type."""

from __future__ import annotations


class Event:
    """An immutable value type representing a named event with an optional payload.

    Raises ValueError if name is not a non-empty str.
    """

    __slots__ = ("name", "payload")

    def __init__(self, name: str, payload=None) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Event name must be a non-empty string, got {name!r}"
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "payload", payload)

    def __setattr__(self, key, value):
        raise AttributeError("Event instances are immutable")

    def __repr__(self) -> str:
        return f"Event(name={self.name!r}, payload={self.payload!r})"
