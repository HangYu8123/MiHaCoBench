"""migrations.py — defines the Migration type for the migration runner."""

from typing import Callable


class Migration:
    """A single versioned migration step with forward (up) and backward (down) operations."""

    def __init__(self, version: int, name: str, up_fn: Callable, down_fn: Callable) -> None:
        self.version: int = version
        self.name: str = name
        self._up_fn = up_fn
        self._down_fn = down_fn

    def up(self, conn) -> None:
        """Apply this migration's forward DDL/DML using the given SQLAlchemy Connection."""
        self._up_fn(conn)

    def down(self, conn) -> None:
        """Reverse this migration's effect using the given Connection."""
        self._down_fn(conn)
