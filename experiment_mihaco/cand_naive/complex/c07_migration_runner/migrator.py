"""migrator.py — Public facade: Migrator (the grader imports THIS file only)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import text

# Re-export Migration so `from migrator import Migrator, Migration` works.
from migrations import Migration


class Migrator:
    """
    Forward/backward schema-migration runner backed by SQLAlchemy 2.0.

    Tracks applied migrations in a ``schema_versions`` bookkeeping table.
    All version ordering is strictly by INTEGER value.
    """

    _BOOKKEEPING_TABLE = "schema_versions"

    def __init__(self, engine) -> None:
        """
        Store the SQLAlchemy Engine. On first use ensure the bookkeeping
        table ``schema_versions`` exists with a single column
        ``version INTEGER PRIMARY KEY``.
        """
        self._engine = engine
        self._migrations: dict[int, Migration] = {}
        self._ensure_bookkeeping_table()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_bookkeeping_table(self) -> None:
        """Create the schema_versions table if it doesn't exist."""
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    f"CREATE TABLE IF NOT EXISTS {self._BOOKKEEPING_TABLE} "
                    f"(version INTEGER PRIMARY KEY)"
                )
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, migration: Migration) -> None:
        """
        Add ``migration`` to the known set.

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
        """
        Return the applied versions, sorted ASCENDING as INTEGERS, read
        from the ``schema_versions`` table.  Empty list when none applied.
        """
        with self._engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT version FROM {self._BOOKKEEPING_TABLE}")
            )
            versions = [row[0] for row in result]
        versions.sort()
        return versions

    def current(self) -> Optional[int]:
        """
        Return the maximum applied version as an int, or ``None`` when no
        migration has been applied.
        """
        with self._engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT MAX(version) FROM {self._BOOKKEEPING_TABLE}")
            )
            row = result.fetchone()
        if row is None or row[0] is None:
            return None
        return int(row[0])

    def upgrade(self, target: Optional[int] = None) -> None:
        """
        Apply every registered migration whose ``version`` is greater than
        ``current()``, in ASCENDING INTEGER order, up to and INCLUDING
        ``target``.  ``target=None`` means apply all pending migrations.

        Each migration runs inside its own transaction: begin, call
        ``migration.up(conn)``, insert its ``version`` into
        ``schema_versions`` in the SAME transaction, then commit.  If
        ``up()`` raises, the transaction is rolled back so the version is
        NOT recorded and any partial changes are undone; the exception
        propagates.

        Idempotent: calling ``upgrade()`` again with nothing pending is a
        no-op.
        """
        current_version = self.current()

        # Collect candidate migrations: version > current (and <= target if given)
        candidates = sorted(
            (v for v in self._migrations if (current_version is None or v > current_version)),
            key=lambda v: v,  # integer sort
        )

        if target is not None:
            candidates = [v for v in candidates if v <= target]

        for version in candidates:
            migration = self._migrations[version]
            # Each migration gets its own transaction
            with self._engine.begin() as conn:
                migration.up(conn)
                conn.execute(
                    text(
                        f"INSERT INTO {self._BOOKKEEPING_TABLE} (version) VALUES (:version)"
                    ),
                    {"version": version},
                )
            # Update current_version so the next iteration's candidate check
            # is still accurate (though candidates list is already fixed above).

    def downgrade(self, target: int) -> None:
        """
        Roll back every applied migration whose ``version`` is greater than
        ``target``, in DESCENDING INTEGER order.

        For each such migration: begin a transaction, call
        ``migration.down(conn)``, delete its ``version`` row from
        ``schema_versions`` in the same transaction, then commit.
        ``target`` may be below the lowest registered version, which rolls
        back everything.
        """
        applied = self.applied_versions()  # sorted ascending

        # We only roll back versions that are applied AND registered AND > target
        to_rollback = sorted(
            (v for v in applied if v > target and v in self._migrations),
            reverse=True,  # descending
        )

        for version in to_rollback:
            migration = self._migrations[version]
            with self._engine.begin() as conn:
                migration.down(conn)
                conn.execute(
                    text(
                        f"DELETE FROM {self._BOOKKEEPING_TABLE} WHERE version = :version"
                    ),
                    {"version": version},
                )
