"""Grader for complex/c07_migration_runner.

Tests the public contract only (see TASK.md). Each test exercises one method
of ``Migrator`` (and the ``Migration`` type) so a partially-correct solution
earns partial credit.

Validity invariant:
  PASSES on the gold reference (all N tests pass).
  FAILS  on the broken reference (>=1 test fails — the integer-ordering tests).

The planted defect in the broken variant orders versions lexicographically
("10" < "2"), so with versions 2 and 10 the v10 migration runs before v2 (its
ALTER fails because the table v2 creates does not yet exist), and
applied_versions()/current() report the wrong order/value.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event, inspect, text

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c07_migration_runner"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the facade module and grab the two public names. Other modules
# (migrations, etc.) are imported transitively; the grader never names them.
_mod = gu.load_module(SOL, "migrator.py")
Migrator = _mod.Migrator
Migration = _mod.Migration


# ---------------------------------------------------------------------------
# Helpers — migration factories used across tests
# ---------------------------------------------------------------------------

def fresh_engine():
    """A fresh in-memory SQLite engine with one shared connection.

    ``StaticPool`` keeps a single underlying connection so the bookkeeping
    table and any migrated tables persist across operations on ``:memory:``.

    The two event hooks install SQLAlchemy's documented pysqlite recipe for
    *transactional DDL*: pysqlite otherwise auto-commits DDL, which would
    prevent a failed migration's ``CREATE TABLE`` from being rolled back. With
    these hooks SQLAlchemy fully controls BEGIN/COMMIT/ROLLBACK so the
    migration runner's standard ``engine.begin()`` transactions behave
    atomically. The runner code under test uses only the plain Engine API.
    """
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _disable_pysqlite_autobegin(dbapi_conn, conn_record):  # noqa: ARG001
        dbapi_conn.isolation_level = None

    @event.listens_for(engine, "begin")
    def _emit_begin(conn):
        conn.exec_driver_sql("BEGIN")

    return engine


def make_v2() -> "Migration":
    """v2: create table widgets(id INTEGER PRIMARY KEY, qty INTEGER)."""

    def up(conn):
        conn.execute(
            text("CREATE TABLE widgets (id INTEGER PRIMARY KEY, qty INTEGER)")
        )

    def down(conn):
        conn.execute(text("DROP TABLE widgets"))

    return Migration(2, "create_widgets", up, down)


def make_v10() -> "Migration":
    """v10: ALTER TABLE widgets ADD COLUMN price INTEGER (needs v2 applied)."""

    def up(conn):
        conn.execute(text("ALTER TABLE widgets ADD COLUMN price INTEGER"))

    def down(conn):
        # SQLite supports DROP COLUMN in modern versions; if unsupported the
        # column simply stays — the bookkeeping row is what the grader checks.
        try:
            conn.execute(text("ALTER TABLE widgets DROP COLUMN price"))
        except Exception:
            pass

    return Migration(10, "add_price", up, down)


def make_simple(version: int) -> "Migration":
    """A self-contained migration creating/dropping its own table."""
    tname = f"t_{version}"

    def up(conn):
        conn.execute(text(f"CREATE TABLE {tname} (id INTEGER PRIMARY KEY)"))

    def down(conn):
        conn.execute(text(f"DROP TABLE {tname}"))

    return Migration(version, f"mk_{tname}", up, down)


def make_boom(version: int) -> "Migration":
    """A migration whose up() partially runs then raises (for rollback tests).

    Keep ``version`` single-digit so the integer-vs-string ordering defect does
    not interfere with this test.
    """

    def up(conn):
        conn.execute(text(f"CREATE TABLE boom_{version} (id INTEGER PRIMARY KEY)"))
        raise RuntimeError("intentional failure inside up()")

    def down(conn):
        conn.execute(text(f"DROP TABLE boom_{version}"))

    return Migration(version, f"boom_{version}", up, down)


def table_exists(engine, name: str) -> bool:
    return inspect(engine).has_table(name)


def column_names(engine, table: str) -> list[str]:
    return [c["name"] for c in inspect(engine).get_columns(table)]


# ---------------------------------------------------------------------------
# PASS_TO_PASS — these hold for BOTH gold and broken
# ---------------------------------------------------------------------------

def test_register_duplicate_version_raises():
    """register() rejects a second migration with the same version."""
    m = Migrator(fresh_engine())
    m.register(make_simple(3))
    with pytest.raises(ValueError):
        m.register(make_simple(3))


def test_fresh_current_is_none_and_applied_empty():
    """A brand-new Migrator has no applied versions."""
    m = Migrator(fresh_engine())
    assert m.current() is None
    assert m.applied_versions() == []


def test_upgrade_single_records_version():
    """Upgrading one registered migration records and applies it."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_simple(1))
    m.upgrade()
    assert m.applied_versions() == [1]
    assert m.current() == 1
    assert table_exists(eng, "t_1")


def test_idempotent_reupgrade_is_noop():
    """A second upgrade() with nothing pending changes nothing."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_simple(1))
    m.upgrade()
    before = m.applied_versions()
    m.upgrade()  # nothing pending
    assert m.applied_versions() == before == [1]
    assert m.current() == 1


def test_downgrade_single_removes_version():
    """Downgrading below a single applied migration rolls it back."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_simple(5))
    m.upgrade()
    assert m.current() == 5
    assert table_exists(eng, "t_5")

    m.downgrade(0)  # below the lowest version → roll back everything
    assert m.applied_versions() == []
    assert m.current() is None
    assert not table_exists(eng, "t_5")


def test_failing_up_leaves_version_unrecorded():
    """A migration whose up() raises is not recorded and partial work is undone.

    Uses a single-digit version so the ordering defect does not interfere.
    """
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_boom(4))
    with pytest.raises(RuntimeError):
        m.upgrade()
    # Version must NOT be recorded.
    assert 4 not in m.applied_versions()
    assert m.current() is None
    # The partial CREATE TABLE inside the failed transaction must be rolled back.
    assert not table_exists(eng, "boom_4")


def test_register_and_apply_two_independent_single_digit():
    """Two single-digit migrations apply in ascending order (no ordering trap)."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_simple(1))
    m.register(make_simple(3))
    m.upgrade()
    assert m.applied_versions() == [1, 3]
    assert m.current() == 3


# ---------------------------------------------------------------------------
# FAIL_TO_PASS — gold true, broken false (the integer-ordering crux)
# ---------------------------------------------------------------------------

def test_upgrade_orders_by_integer_not_string():
    """v2 then v10 must apply in INTEGER order even when registered reversed.

    Under the lexicographic defect, "10" < "2", so v10 runs first and its
    ALTER fails (widgets does not exist yet) or the schema ends up wrong.
    """
    eng = fresh_engine()
    m = Migrator(eng)
    # Register in REVERSED order: 10 first, then 2.
    m.register(make_v10())
    m.register(make_v2())

    m.upgrade(None)

    # Both migrations applied, in integer order.
    assert m.applied_versions() == [2, 10]
    # widgets exists and has the price column added by v10.
    assert table_exists(eng, "widgets")
    cols = column_names(eng, "widgets")
    assert "qty" in cols
    assert "price" in cols


def test_current_is_integer_max_not_string_max():
    """current() must be 10 (integer max), not 2 (string max)."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_v10())
    m.register(make_v2())
    m.upgrade(None)
    assert m.current() == 10


def test_applied_versions_sorted_as_integers():
    """applied_versions() must be [2, 10], not the lexicographic [10, 2]."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_v2())
    m.register(make_v10())
    m.upgrade(None)
    assert m.applied_versions() == [2, 10]


def test_downgrade_then_upgrade_roundtrip():
    """downgrade(2) then upgrade() round-trips with correct integer ordering."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_v10())
    m.register(make_v2())
    m.upgrade(None)
    assert m.applied_versions() == [2, 10]

    # Roll back everything above version 2 → only v10 reverts.
    m.downgrade(2)
    assert m.applied_versions() == [2]
    assert m.current() == 2
    assert "price" not in column_names(eng, "widgets")

    # Re-upgrade should re-apply v10 (and only v10) in integer order.
    m.upgrade()
    assert m.applied_versions() == [2, 10]
    assert m.current() == 10
    assert "price" in column_names(eng, "widgets")


def test_upgrade_target_stops_at_target():
    """upgrade(target=2) applies v2 but not v10 even when both registered."""
    eng = fresh_engine()
    m = Migrator(eng)
    m.register(make_v10())
    m.register(make_v2())
    m.upgrade(target=2)
    assert m.applied_versions() == [2]
    assert m.current() == 2
    assert table_exists(eng, "widgets")
    assert "price" not in column_names(eng, "widgets")


# ---------------------------------------------------------------------------
# Advisory code-quality test (never asserted, just reported)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
