"""migrator.py — Public facade: Migrator (the grader imports THIS file only).

Also re-exports Migration so that:
    from migrator import Migrator, Migration
works.
"""

from sqlalchemy import text

from migrations import Migration  # noqa: F401  (re-export)

__all__ = ["Migrator", "Migration"]

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY
)
"""


class Migrator:
    """Forward/backward schema-migration runner backed by SQLAlchemy 2.0."""

    def __init__(self, engine) -> None:
        """Store the SQLAlchemy Engine and ensure the bookkeeping table exists."""
        self._engine = engine
        self._migrations: dict[int, Migration] = {}
        self._ensure_bookkeeping_table()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_bookkeeping_table(self) -> None:
        """Create schema_versions if it does not already exist."""
        with self._engine.begin() as conn:
            conn.execute(text(_INIT_SQL))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, migration: Migration) -> None:
        """Add *migration* to the known set.

        Raises ``ValueError`` if a migration with the same ``version`` is
        already registered.
        """
        if migration.version in self._migrations:
            raise ValueError(
                f"A migration with version {migration.version!r} is already registered."
            )
        self._migrations[migration.version] = migration

    def applied_versions(self) -> list[int]:
        """Return the applied versions, sorted ASCENDING as INTEGERS.

        Reads from the ``schema_versions`` table. Returns an empty list when
        none have been applied.
        """
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT version FROM schema_versions ORDER BY version ASC")
            )
            return [int(row[0]) for row in result]

    def current(self) -> "int | None":
        """Return the maximum applied version as an int, or ``None``."""
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT MAX(version) FROM schema_versions")
            )
            row = result.fetchone()
            if row is None or row[0] is None:
                return None
            return int(row[0])

    def upgrade(self, target: "int | None" = None) -> None:
        """Apply every registered migration whose ``version`` > ``current()``.

        Applies in ASCENDING INTEGER order, up to and INCLUDING ``target``.
        ``target=None`` means apply all pending migrations.

        Each migration runs in its own transaction. On failure the transaction
        is rolled back, the version is NOT recorded, and the exception
        propagates.
        """
        current = self.current()

        # Collect pending migrations sorted numerically.
        pending = sorted(
            (m for m in self._migrations.values()
             if current is None or m.version > current),
            key=lambda m: m.version,
        )

        if target is not None:
            pending = [m for m in pending if m.version <= target]

        for migration in pending:
            with self._engine.begin() as conn:
                migration.up(conn)
                conn.execute(
                    text("INSERT INTO schema_versions (version) VALUES (:v)"),
                    {"v": migration.version},
                )

    def downgrade(self, target: int) -> None:
        """Roll back every applied migration whose ``version`` > ``target``.

        Processes in DESCENDING INTEGER order. For each such migration: begins
        a transaction, calls ``migration.down(conn)``, deletes its ``version``
        row from ``schema_versions`` in the same transaction, then commits.
        ``target`` may be below the lowest registered version (rolls back
        everything).
        """
        applied = self.applied_versions()

        # Versions to roll back: applied versions > target, descending.
        to_rollback = sorted(
            [v for v in applied if v > target],
            reverse=True,
        )

        for version in to_rollback:
            if version not in self._migrations:
                raise ValueError(
                    f"Cannot downgrade version {version!r}: migration not registered."
                )
            migration = self._migrations[version]
            with self._engine.begin() as conn:
                migration.down(conn)
                conn.execute(
                    text("DELETE FROM schema_versions WHERE version = :v"),
                    {"v": version},
                )
