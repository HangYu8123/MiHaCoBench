"""events.py — Event value type for the publish/subscribe event bus."""

from typing import Any


class Event:
    """An immutable value type representing a named event with an optional payload."""

    __slots__ = ("_name", "_payload")

    def __init__(self, name: str, payload: Any = None) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Event name must be a non-empty string, got {name!r}"
            )
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_payload", payload)

    @property
    def name(self) -> str:
        return self._name

    @property
    def payload(self) -> Any:
        return self._payload

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("Event is immutable")

    def __delattr__(self, key: str) -> None:
        raise AttributeError("Event is immutable")

    def __repr__(self) -> str:
        return f"Event(name={self._name!r}, payload={self._payload!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return self._name == other._name and self._payload == other._payload

    def __hash__(self) -> int:
        return hash((self._name, id(self._payload)))
