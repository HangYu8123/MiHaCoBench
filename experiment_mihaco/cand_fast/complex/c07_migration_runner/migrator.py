"""migrator.py — public facade for the schema-migration runner.

Re-exports Migration so that:
    from migrator import Migrator, Migration
works.
"""

from __future__ import annotations

from sqlalchemy import text

from migrations import Migration  # re-export

__all__ = ["Migrator", "Migration"]


class Migrator:
    """Forward/backward schema-migration runner backed by SQLAlchemy 2.0."""

    def __init__(self, engine) -> None:
        """Store the SQLAlchemy Engine and ensure the bookkeeping table exists."""
        self._engine = engine
        self._migrations: dict[int, Migration] = {}
        self._ensure_table()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_table(self) -> None:
        """Create schema_versions table if it does not already exist."""
        with self._engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS schema_versions "
                    "(version INTEGER PRIMARY KEY)"
                )
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, migration: Migration) -> None:
        """Add migration to the known set.

        Raises ValueError if a migration with the same version is already
        registered.
        """
        if migration.version in self._migrations:
            raise ValueError(
                f"A migration with version {migration.version} is already registered."
            )
        self._migrations[migration.version] = migration

    def applied_versions(self) -> list[int]:
        """Return applied versions sorted ASCENDING as integers."""
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT version FROM schema_versions ORDER BY version ASC")
            )
            return [int(row[0]) for row in result]

    def current(self) -> int | None:
        """Return the maximum applied version as int, or None if none applied."""
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT MAX(version) FROM schema_versions")
            )
            row = result.fetchone()
            if row is None or row[0] is None:
                return None
            return int(row[0])

    def upgrade(self, target: int | None = None) -> None:
        """Apply every registered migration whose version > current(), in
        ascending integer order, up to and including target.

        target=None means apply all pending migrations.
        Each migration runs in its own transaction; on failure the transaction
        is rolled back and the exception propagates.
        """
        current = self.current()

        # Collect pending migrations: version > current and version <= target
        pending = sorted(
            (m for v, m in self._migrations.items()
             if (current is None or v > current)
             and (target is None or v <= target)),
            key=lambda m: m.version,
        )

        for migration in pending:
            # engine.begin() auto-commits on success, auto-rolls back on exception
            with self._engine.begin() as conn:
                migration.up(conn)
                conn.execute(
                    text("INSERT INTO schema_versions(version) VALUES (:v)"),
                    {"v": migration.version},
                )

    def downgrade(self, target: int) -> None:
        """Roll back every applied migration whose version > target, in
        descending integer order.

        target may be below the lowest registered version, rolling back everything.
        """
        applied = self.applied_versions()  # already sorted ascending

        # Versions to roll back: version > target, in descending order
        to_rollback = sorted(
            [v for v in applied if v > target],
            reverse=True,
        )

        for version in to_rollback:
            if version not in self._migrations:
                # No registered migration for this version; skip (or raise?)
                # Spec doesn't say — skip gracefully
                continue
            migration = self._migrations[version]
            with self._engine.begin() as conn:
                migration.down(conn)
                conn.execute(
                    text("DELETE FROM schema_versions WHERE version = :v"),
                    {"v": version},
                )
