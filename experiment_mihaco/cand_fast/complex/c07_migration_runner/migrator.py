"""migrator.py — public facade: Migrator class for schema-migration runner."""

from sqlalchemy import text

from migrations import Migration


class Migrator:
    """Forward/backward schema-migration runner backed by SQLAlchemy 2.0."""

    def __init__(self, engine) -> None:
        """Store the SQLAlchemy Engine. Bookkeeping table is lazily ensured on first use."""
        self._engine = engine
        self._registry: dict[int, Migration] = {}

    def _ensure_bookkeeping(self, conn) -> None:
        """Create schema_versions table if it does not already exist (idempotent)."""
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_versions "
            "(version INTEGER PRIMARY KEY)"
        ))

    def register(self, migration: Migration) -> None:
        """Add migration to the known set.

        Raises ValueError if a migration with the same version is already registered.
        """
        version = int(migration.version)
        if version in self._registry:
            raise ValueError(
                f"A migration with version {version!r} is already registered."
            )
        self._registry[version] = migration

    def applied_versions(self) -> list[int]:
        """Return applied versions sorted ASCENDING as integers from schema_versions."""
        with self._engine.begin() as conn:
            self._ensure_bookkeeping(conn)
            result = conn.execute(text("SELECT version FROM schema_versions"))
            versions = [int(row[0]) for row in result]
        return sorted(versions)

    def current(self) -> int | None:
        """Return the maximum applied version as an int, or None if none applied."""
        versions = self.applied_versions()
        return max(versions) if versions else None

    def upgrade(self, target: int | None = None) -> None:
        """Apply every pending registered migration in ascending integer order.

        'Pending' means version > current() and, if target is given, <= target.
        Each migration runs in its own transaction; on failure the transaction
        rolls back and the exception propagates.
        """
        current = self.current()

        # Collect pending versions: registered versions greater than current
        pending = [v for v in self._registry if current is None or v > current]

        # Apply upper bound if target is specified
        if target is not None:
            pending = [v for v in pending if v <= target]

        # Sort ascending by integer value
        pending.sort()

        for v in pending:
            migration = self._registry[v]
            with self._engine.begin() as conn:
                self._ensure_bookkeeping(conn)
                migration.up(conn)
                conn.execute(
                    text("INSERT INTO schema_versions (version) VALUES (:version)"),
                    {"version": v},
                )

    def downgrade(self, target: int) -> None:
        """Roll back every applied migration with version > target, descending order.

        Each migration runs in its own transaction; on failure the transaction
        rolls back and the exception propagates.
        """
        applied = self.applied_versions()

        # Versions to roll back: applied versions greater than target
        to_rollback = [v for v in applied if v > target]

        # Sort descending by integer value (roll back newest first)
        to_rollback.sort(reverse=True)

        for v in to_rollback:
            if v not in self._registry:
                raise RuntimeError(
                    f"Migration version {v!r} was applied but is not registered; "
                    "cannot roll back."
                )
            migration = self._registry[v]
            with self._engine.begin() as conn:
                self._ensure_bookkeeping(conn)
                migration.down(conn)
                conn.execute(
                    text("DELETE FROM schema_versions WHERE version = :version"),
                    {"version": v},
                )
