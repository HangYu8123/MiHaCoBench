"""migrations.py — Migration type for the schema-migration runner."""


class Migration:
    """A single versioned migration step.

    Parameters
    ----------
    version : int
        The integer version number of this migration.
    name : str
        A human-readable label.
    up_fn : callable
        A function ``up_fn(conn) -> None`` that applies the forward DDL/DML.
    down_fn : callable
        A function ``down_fn(conn) -> None`` that reverses the migration.
    """

    def __init__(self, version: int, name: str, up_fn, down_fn) -> None:
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

    def __repr__(self) -> str:
        return f"Migration(version={self.version!r}, name={self.name!r})"
