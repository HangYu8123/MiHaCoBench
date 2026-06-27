"""
migrator.py — Public facade: Migrator class for schema-migration management.

Re-exports Migration so that ``from migrator import Migrator, Migration`` works.
"""
from __future__ import annotations

from sqlalchemy import text

from migrations import Migration  # re-exported below


class Migrator:
    """Forward/backward schema-migration runner backed by SQLAlchemy 2.0.

    Maintains an ordered set of migrations and applies or rolls them back
    in integer version order, tracking applied versions in a
    ``schema_versions`` bookkeeping table within the provided engine.

    Parameters
    ----------
    engine :
        A SQLAlchemy ``Engine`` instance. The caller is responsible for
        creating and configuring the engine (e.g. StaticPool for in-memory
        SQLite). This class never creates its own engine.
    """

    def __init__(self, engine) -> None:
        self._engine = engine
        self._migrations: dict[int, Migration] = {}
        # Eagerly create the bookkeeping table so it exists for all operations.
        with engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS schema_versions "
                    "(version INTEGER PRIMARY KEY)"
                )
            )

    def register(self, migration: Migration) -> None:
        """Add *migration* to the known set.

        Raises
        ------
        ValueError
            If a migration with the same ``version`` is already registered.
        """
        if migration.version in self._migrations:
            raise ValueError(
                f"A migration with version {migration.version!r} is already registered."
            )
        self._migrations[migration.version] = migration

    def applied_versions(self) -> list[int]:
        """Return applied versions sorted ascending as integers.

        Reads from the ``schema_versions`` table. Returns an empty list
        when no migrations have been applied.
        """
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT version FROM schema_versions ORDER BY version ASC")
            )
            return [int(row[0]) for row in result]

    def current(self) -> int | None:
        """Return the maximum applied version as an int, or ``None``."""
        versions = self.applied_versions()
        return max(versions) if versions else None

    def upgrade(self, target: int | None = None) -> None:
        """Apply every pending registered migration up to *target*.

        Applies migrations whose ``version`` is greater than ``current()``
        (and ``<= target`` if *target* is given), in ascending integer order.

        Each migration runs in its own transaction. On failure the transaction
        is rolled back and the exception propagates; the version is NOT
        recorded.

        Idempotent: a no-op when nothing is pending.
        """
        current_version = self.current()
        current_version = current_version if current_version is not None else 0

        pending = sorted(
            v for v in self._migrations
            if v > current_version and (target is None or v <= target)
        )

        for v in pending:
            migration = self._migrations[v]
            with self._engine.begin() as conn:
                migration.up(conn)
                conn.execute(
                    text("INSERT INTO schema_versions(version) VALUES (:v)"),
                    {"v": v},
                )

    def downgrade(self, target: int) -> None:
        """Roll back applied migrations whose ``version`` is greater than *target*.

        Processes in descending integer order. Each rollback runs in its own
        transaction.

        Raises
        ------
        ValueError
            If an applied version has no registered migration (cannot roll back).
        """
        to_rollback = sorted(
            (v for v in self.applied_versions() if v > target),
            reverse=True,
        )

        for v in to_rollback:
            if v not in self._migrations:
                raise ValueError(
                    f"Cannot roll back version {v!r}: no migration registered for it."
                )
            migration = self._migrations[v]
            with self._engine.begin() as conn:
                migration.down(conn)
                conn.execute(
                    text("DELETE FROM schema_versions WHERE version = :v"),
                    {"v": v},
                )


__all__ = ["Migrator", "Migration"]
