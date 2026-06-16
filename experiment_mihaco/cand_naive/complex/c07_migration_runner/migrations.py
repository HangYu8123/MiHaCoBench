"""migrations.py — Migration type for the schema-migration runner."""

from typing import Callable, Any


class Migration:
    """A single versioned migration step with forward (up) and backward (down) operations."""

    def __init__(
        self,
        version: int,
        name: str,
        up_fn: Callable[[Any], None],
        down_fn: Callable[[Any], None],
    ) -> None:
        """
        Create a Migration.

        Parameters
        ----------
        version : int
            The integer version number of this migration.
        name : str
            A human-readable label.
        up_fn : callable
            A callable ``up_fn(conn)`` that applies the migration using a
            SQLAlchemy Connection.
        down_fn : callable
            A callable ``down_fn(conn)`` that reverses the migration using a
            SQLAlchemy Connection.
        """
        self.version = version
        self.name = name
        self._up_fn = up_fn
        self._down_fn = down_fn

    def up(self, conn: Any) -> None:
        """Apply this migration's forward DDL/DML using the given SQLAlchemy Connection."""
        self._up_fn(conn)

    def down(self, conn: Any) -> None:
        """Reverse this migration's effect using the given Connection."""
        self._down_fn(conn)

    def __repr__(self) -> str:
        return f"Migration(version={self.version!r}, name={self.name!r})"
