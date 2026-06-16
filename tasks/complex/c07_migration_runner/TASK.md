# Complex 07 — `migration_runner`: SQLAlchemy Schema-Migration Runner

**Created:** 2026-06-16 · **Category:** complex · **Weight:** 5

Implement a forward/backward schema-migration runner backed by **SQLAlchemy
2.0** and the **standard library only** (no other third-party packages). A
caller hands you a SQLAlchemy `Engine`; you maintain an ordered set of
migrations and apply or roll them back in **integer version order**, tracking
which versions have been applied in a `schema_versions` bookkeeping table.

Structure your solution as multiple modules:

```
migrations.py   — the Migration type (a single versioned migration step)
migrator.py     — public facade: Migrator (the grader imports THIS file only)
```

You may add additional helper modules; the grader only imports `migrator.py`.

Use an in-memory SQLite engine for testing, e.g. `create_engine("sqlite://")`,
which the grader constructs and passes in — your code must NOT create its own
engine.

## Public contract

### `migrations.py` — `class Migration`

```python
class Migration:
    version: int          # the integer version number of this migration
    name: str             # a human-readable label

    def up(self, conn) -> None:
        """Apply this migration's forward DDL/DML using the given
        SQLAlchemy Connection (e.g. conn.execute(text("CREATE TABLE ..."))).
        """

    def down(self, conn) -> None:
        """Reverse this migration's effect using the given Connection."""
```

A `Migration` is constructed from a `version: int`, a `name: str`, and two
callables `up(conn)` and `down(conn)` that receive a live SQLAlchemy
`Connection` and run statements via `conn.execute(text(...))`. The exact
constructor signature is up to you, but instances MUST expose the public
attributes `version` (int) and `name` (str) and the methods `up(conn)` /
`down(conn)`.

`migrator.py` must re-export `Migration` so that
`from migrator import Migrator, Migration` works.

### `migrator.py` — `class Migrator`

```python
class Migrator:
    def __init__(self, engine) -> None:
        """Store the SQLAlchemy Engine. On first use ensure a bookkeeping
        table ``schema_versions`` exists with a single column
        ``version INTEGER PRIMARY KEY``.
        """

    def register(self, migration: "Migration") -> None:
        """Add ``migration`` to the known set.
        Raise ``ValueError`` if a migration with the same ``version`` is
        already registered (duplicate version).
        """

    def applied_versions(self) -> list[int]:
        """Return the applied versions, sorted ASCENDING as INTEGERS, read
        from the ``schema_versions`` table. Empty list when none applied.
        """

    def current(self) -> int | None:
        """Return the maximum applied version as an int, or ``None`` when no
        migration has been applied.
        """

    def upgrade(self, target: int | None = None) -> None:
        """Apply every registered migration whose ``version`` is greater than
        ``current()``, in ASCENDING INTEGER order, up to and INCLUDING
        ``target``. ``target=None`` means apply all pending migrations.

        Each migration runs inside its own transaction: begin, call
        ``migration.up(conn)``, insert its ``version`` into
        ``schema_versions`` in the SAME transaction, then commit. If
        ``up()`` raises, the transaction is rolled back so the version is NOT
        recorded and any partial changes are undone; the exception propagates.

        Idempotent: calling ``upgrade()`` again with nothing pending is a
        no-op.
        """

    def downgrade(self, target: int) -> None:
        """Roll back every applied migration whose ``version`` is greater than
        ``target``, in DESCENDING INTEGER order. For each such migration:
        begin a transaction, call ``migration.down(conn)``, delete its
        ``version`` row from ``schema_versions`` in the same transaction, then
        commit. ``target`` may be below the lowest registered version, which
        rolls back everything.
        """
```

## Ordering requirement (the crux)

All ordering — in `upgrade`, `downgrade`, `applied_versions`, and `current` —
is by **INTEGER** version, never by string/lexicographic order. With versions
`2` and `10` registered, `upgrade()` must apply `2` **before** `10`,
`applied_versions()` must return `[2, 10]` (not `[10, 2]`), and `current()`
must return `10` (not `2`). Migrations may be registered in any order; the
runner sorts them numerically.

## Notes

- A migration's `up()` and `down()` execute via the passed `Connection`; do
  not open your own connection from inside `up`/`down`.
- `upgrade(target)` applies migrations with `current() < version <= target`.
- `downgrade(target)` rolls back migrations with `version > target`.
- Determinism: given identical registrations and calls, results are identical.
- Only one engine is involved; for in-memory SQLite use a single shared
  connection pool so the bookkeeping table persists across operations.
