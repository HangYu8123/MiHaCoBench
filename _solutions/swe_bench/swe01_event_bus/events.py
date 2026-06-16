"""events.py — Event value type for the in-memory publish/subscribe bus.

An Event is an immutable value object carrying an event name and an arbitrary
payload.  Handler return values are collected by the bus and returned to the
publisher as a list.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    """Immutable event value type.

    Attributes
    ----------
    name:
        The logical channel name (e.g. ``"user.created"``).
    payload:
        Arbitrary data attached to the event.  Defaults to ``None``.
    """

    name: str
    payload: Any = field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError(f"Event.name must be a non-empty string, got {self.name!r}")
