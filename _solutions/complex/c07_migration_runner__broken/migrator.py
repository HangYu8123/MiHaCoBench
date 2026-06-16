"""Public facade for the schema-migration runner (BROKEN variant).

Planted defect: version ordering uses STRING/lexicographic sort instead of
integer ordering. ``upgrade`` sorts pending migrations by ``str(version)`` and
``current()`` / ``applied_versions()`` compute max/sort over the string form.

With versions 2 and 10 present, ``"10" < "2"`` lexically, so v10 is applied
BEFORE v2 (its ALTER fails because the table v2 creates does not exist yet),
and ``applied_versions()`` / ``current()`` report the wrong order/value. The
bug only manifests once a version >= 10 coexists with a single-digit version.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Re-export Migration so callers can do ``from migrator import Migrator, Migration``.
from migrations import Migration  # noqa: F401

__all__ = ["Migrator", "Migration"]


class Migrator:
    """Forward/backward schema-migration runner over a SQLAlchemy Engine."""

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

        Raises ``ValueError`` on a duplicate version.
        """
        version = int(migration.version)
        if version in self._migrations:
            raise ValueError(f"duplicate migration version: {version}")
        self._migrations[version] = migration

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def applied_versions(self) -> list[int]:
        """Return applied versions sorted by their STRING form (DEFECT)."""
        self._ensure_bookkeeping()
        with self._engine.connect() as conn:
            rows = conn.execute(text("SELECT version FROM schema_versions")).all()
        # DEFECT: sort lexicographically by str(version) instead of numerically.
        ordered = sorted((int(r[0]) for r in rows), key=lambda v: str(v))
        return ordered

    def current(self) -> Optional[int]:
        """Return the version that is maximal by STRING comparison (DEFECT)."""
        applied = self.applied_versions()
        if not applied:
            return None
        # DEFECT: max over the string form, e.g. "2" > "10".
        return max(applied, key=lambda v: str(v))

    # ------------------------------------------------------------------
    # Forward / backward
    # ------------------------------------------------------------------

    def upgrade(self, target: Optional[int] = None) -> None:
        """Apply pending migrations in lexicographic version order (DEFECT)."""
        cur = self.current()
        floor = cur if cur is not None else None

        # DEFECT: sort registered versions by str(version), so 10 sorts before 2.
        for version in sorted(self._migrations.keys(), key=lambda v: str(v)):
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
        """Roll back applied migrations with version > ``target`` (DEFECT order)."""
        applied = self.applied_versions()
        # DEFECT: descending by string form.
        for version in sorted(applied, key=lambda v: str(v), reverse=True):
            if version <= target:
                continue
            migration = self._migrations.get(version)
            if migration is None:
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
