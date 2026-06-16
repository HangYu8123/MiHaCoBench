"""migrations.py — defines the Migration type for the migration runner."""

from __future__ import annotations
from typing import Callable


class Migration:
    """A single versioned migration step with a forward (up) and backward (down) operation."""

    def __init__(
        self,
        version: int,
        name: str,
        up: Callable,
        down: Callable,
    ) -> None:
        self.version: int = int(version)
        self.name: str = name
        self._up = up
        self._down = down

    def up(self, conn) -> None:
        """Apply this migration's forward DDL/DML using the given SQLAlchemy Connection."""
        self._up(conn)

    def down(self, conn) -> None:
        """Reverse this migration's effect using the given Connection."""
        self._down(conn)

    def __repr__(self) -> str:
        return f"Migration(version={self.version}, name={self.name!r})"
