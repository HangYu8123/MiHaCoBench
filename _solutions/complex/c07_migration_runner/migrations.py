"""The Migration type for the schema-migration runner.

A :class:`Migration` is a single versioned migration step. It bundles an
integer ``version``, a human-readable ``name``, and two callables ``up`` and
``down`` that receive a live SQLAlchemy :class:`~sqlalchemy.engine.Connection`
and execute DDL/DML via ``conn.execute(text(...))``.

The runner (see ``migrator.py``) is responsible for ordering migrations by
integer version and for the transaction/bookkeeping around each call.
"""
from __future__ import annotations

from typing import Callable


# A migration callable takes a SQLAlchemy Connection and returns None.
MigrationFn = Callable[["object"], None]


class Migration:
    """A single, versioned schema migration.

    Parameters
    ----------
    version:
        The integer version number. Migrations are applied in ascending
        integer order of this value.
    name:
        A human-readable label (purely descriptive).
    up:
        Callable ``up(conn)`` that applies the forward change using the
        supplied SQLAlchemy ``Connection``.
    down:
        Callable ``down(conn)`` that reverses the change using the supplied
        ``Connection``.
    """

    def __init__(
        self,
        version: int,
        name: str,
        up: MigrationFn,
        down: MigrationFn,
    ) -> None:
        # Store version strictly as an int so ordering is numeric everywhere.
        self.version: int = int(version)
        self.name: str = str(name)
        self._up: MigrationFn = up
        self._down: MigrationFn = down

    def up(self, conn) -> None:
        """Apply the forward migration on ``conn``."""
        self._up(conn)

    def down(self, conn) -> None:
        """Reverse the migration on ``conn``."""
        self._down(conn)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Migration version={self.version} name={self.name!r}>"
