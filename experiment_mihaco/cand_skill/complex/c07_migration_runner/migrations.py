"""
migrations.py — Migration type for the schema-migration runner.
"""
from __future__ import annotations

from typing import Callable


class Migration:
    """A single versioned migration step.

    Parameters
    ----------
    version : int
        The integer version number of this migration.
    name : str
        A human-readable label.
    up_fn : Callable
        Called with a live SQLAlchemy Connection to apply the migration.
    down_fn : Callable
        Called with a live SQLAlchemy Connection to reverse the migration.
    """

    def __init__(
        self,
        version: int,
        name: str,
        up_fn: Callable,
        down_fn: Callable,
    ) -> None:
        self.version: int = version
        self.name: str = name
        self._up_fn = up_fn
        self._down_fn = down_fn

    def up(self, conn) -> None:
        """Apply this migration's forward DDL/DML using the given Connection."""
        self._up_fn(conn)

    def down(self, conn) -> None:
        """Reverse this migration's effect using the given Connection."""
        self._down_fn(conn)
