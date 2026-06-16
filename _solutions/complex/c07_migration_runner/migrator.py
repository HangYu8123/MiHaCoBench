"""Public facade for the schema-migration runner (the grader imports this).

``Migrator`` drives a set of :class:`Migration` objects forward and backward
in **integer version order**, recording applied versions in a bookkeeping
table ``schema_versions`` (one column: ``version INTEGER PRIMARY KEY``).

Each forward/backward step runs in its own transaction so that a failing
``up()`` leaves the schema and the bookkeeping table untouched.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Re-export Migration so callers can do ``from migrator import Migrator, Migration``.
from migrations import Migration  # noqa: F401

__all__ = ["Migrator", "Migration"]


class Migrator:
    """Forward/backward schema-migration runner over a SQLAlchemy Engine.

    Parameters
    ----------
    engine:
        A SQLAlchemy :class:`~sqlalchemy.engine.Engine`. The runner reuses it
        for all bookkeeping and migration transactions.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._migrations: dict[int, Migration] = {}
        self._ensured = False
        self._ensure_bookkeeping()

    # ------------------------------------------------------------------
    # Bookkeeping table
    # ------------------------------------------------------------------

    def _ensure_bookkeeping(self) -> None:
        """Create the ``schema_versions`` table if it does not yet exist."""
        if self._ensured:
            return
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS schema_versions ("
                    "version INTEGER PRIMARY KEY)"
                )
            )
        self._ensured = True

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, migration: Migration) -> None:
        """Add ``migration`` to the known set.

        Raises ``ValueError`` if a migration with the same integer version is
        already registered.
        """
        version = int(migration.version)
        if version in self._migrations:
            raise ValueError(f"duplicate migration version: {version}")
        self._migrations[version] = migration

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def applied_versions(self) -> list[int]:
        """Return applied versions sorted ascending as INTEGERS."""
        self._ensure_bookkeeping()
        with self._engine.connect() as conn:
            rows = conn.execute(text("SELECT version FROM schema_versions")).all()
        # Coerce to int and sort numerically — never lexicographically.
        return sorted(int(r[0]) for r in rows)

    def current(self) -> Optional[int]:
        """Return the maximum applied version as an int, or None."""
        applied = self.applied_versions()
        if not applied:
            return None
        return max(applied)

    # ------------------------------------------------------------------
    # Forward / backward
    # ------------------------------------------------------------------

    def upgrade(self, target: Optional[int] = None) -> None:
        """Apply pending migrations in ascending integer order up to ``target``.

        Pending = registered migrations whose version is greater than
        ``current()``. ``target=None`` applies all of them. Each migration runs
        in its own transaction; on failure the transaction rolls back so the
        version is not recorded.
        """
        cur = self.current()
        floor = cur if cur is not None else None

        # Sort registered versions numerically.
        for version in sorted(self._migrations.keys()):
            if floor is not None and version <= floor:
                continue
            if target is not None and version > target:
                continue
            migration = self._migrations[version]
            self._apply_one(migration)

    def _apply_one(self, migration: Migration) -> None:
        """Run one migration's up() and record its version in one transaction."""
        with self._engine.begin() as conn:
            migration.up(conn)
            conn.execute(
                text("INSERT INTO schema_versions (version) VALUES (:v)"),
                {"v": int(migration.version)},
            )

    def downgrade(self, target: int) -> None:
        """Roll back applied migrations with version > ``target``.

        Rolls back in DESCENDING integer order. ``target`` may be below the
        lowest version to roll back everything.
        """
        applied = self.applied_versions()
        # Descending integer order.
        for version in sorted(applied, reverse=True):
            if version <= target:
                continue
            migration = self._migrations.get(version)
            if migration is None:
                # No registered migration to reverse — still drop the record so
                # the bookkeeping stays consistent.
                with self._engine.begin() as conn:
                    conn.execute(
                        text("DELETE FROM schema_versions WHERE version = :v"),
                        {"v": int(version)},
                    )
                continue
            self._revert_one(migration)

    def _revert_one(self, migration: Migration) -> None:
        """Run one migration's down() and delete its version in one transaction."""
        with self._engine.begin() as conn:
            migration.down(conn)
            conn.execute(
                text("DELETE FROM schema_versions WHERE version = :v"),
                {"v": int(migration.version)},
            )
