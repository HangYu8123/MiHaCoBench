"""Grader for harness/h07_minisql.

Tests the public contract only (see TASK.md): a single ``Database`` class with
an ``execute(sql)`` method. Validity invariant: PASSES on the gold reference
(every test), FAILS on the broken reference (>=1 test).

Each test exercises one feature/edge-case so partial credit reflects exactly
which rules an arm implemented. Expected values are hand-written from the
contract — the gold is never imported to compute them. All inputs are built
deterministically inline (no committed data).

The planted defect in the broken reference inverts the NULL ordering rule
(NULLs LAST under ASC / FIRST under DESC). The tests marked ``[FAIL_TO_PASS]``
target exactly that rule; every other test still passes on the broken variant.
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h07_minisql"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

Database = getattr(gu.load_module(SOL, "solution.py"), "Database")


# --------------------------------------------------------------------------- #
# Helpers: build deterministic databases inline.
# --------------------------------------------------------------------------- #
def _people_db():
    """A 4-row table with two NULL scores, used across many tests.

    Canonical contents (id, name, score):
        (1, 'alice', 10) (2, 'bob', None) (3, 'cara', 20) (4, 'dan', None)
    """
    db = Database()
    db.execute("CREATE TABLE t (id INT, name TEXT, score INT)")
    db.execute("INSERT INTO t (id, name, score) VALUES (1, 'alice', 10)")
    db.execute("INSERT INTO t VALUES (2, 'bob', NULL)")
    db.execute("INSERT INTO t (id, name, score) VALUES (3, 'cara', 20)")
    db.execute("INSERT INTO t (id, name) VALUES (4, 'dan')")
    return db


def _group_db():
    """Grouping table (g, v): a={1,3,NULL}, b={5}, c={NULL}."""
    db = Database()
    db.execute("CREATE TABLE s (g TEXT, v INT)")
    for g, v in [("a", 1), ("a", 3), ("a", None), ("b", 5), ("c", None)]:
        vv = "NULL" if v is None else str(v)
        db.execute(f"INSERT INTO s VALUES ('{g}', {vv})")
    return db


# --------------------------------------------------------------------------- #
# CREATE / INSERT
# --------------------------------------------------------------------------- #
def test_create_returns_none_and_select_empty():
    db = Database()
    assert db.execute("CREATE TABLE t (id INT, name TEXT)") is None
    assert db.execute("SELECT * FROM t") == []


def test_create_duplicate_table_raises():
    db = Database()
    db.execute("CREATE TABLE t (id INT)")
    with pytest.raises(ValueError):
        db.execute("CREATE TABLE t (id INT)")


def test_insert_returns_none():
    db = Database()
    db.execute("CREATE TABLE t (id INT)")
    assert db.execute("INSERT INTO t VALUES (1)") is None


def test_insert_named_and_positional_and_defaults():
    db = _people_db()
    rows = db.execute("SELECT * FROM t")
    assert rows == [
        {"id": 1, "name": "alice", "score": 10},
        {"id": 2, "name": "bob", "score": None},
        {"id": 3, "name": "cara", "score": 20},
        {"id": 4, "name": "dan", "score": None},  # score omitted -> NULL
    ]


def test_insert_negative_int_and_escaped_quote_literals():
    db = Database()
    db.execute("CREATE TABLE t (n INT, s TEXT)")
    db.execute("INSERT INTO t VALUES (-7, 'it''s')")
    assert db.execute("SELECT * FROM t") == [{"n": -7, "s": "it's"}]


def test_insert_type_mismatch_int_column_raises():
    db = Database()
    db.execute("CREATE TABLE t (n INT)")
    with pytest.raises(ValueError):
        db.execute("INSERT INTO t VALUES ('not an int')")


def test_insert_type_mismatch_text_column_raises():
    db = Database()
    db.execute("CREATE TABLE t (s TEXT)")
    with pytest.raises(ValueError):
        db.execute("INSERT INTO t VALUES (5)")


def test_insert_null_accepted_in_both_column_types():
    db = Database()
    db.execute("CREATE TABLE t (n INT, s TEXT)")
    assert db.execute("INSERT INTO t VALUES (NULL, NULL)") is None
    assert db.execute("SELECT * FROM t") == [{"n": None, "s": None}]


def test_insert_unknown_table_raises():
    db = Database()
    with pytest.raises(ValueError):
        db.execute("INSERT INTO nope VALUES (1)")


def test_insert_unknown_column_raises():
    db = Database()
    db.execute("CREATE TABLE t (id INT)")
    with pytest.raises(ValueError):
        db.execute("INSERT INTO t (zzz) VALUES (1)")


def test_insert_wrong_value_count_raises():
    db = Database()
    db.execute("CREATE TABLE t (a INT, b INT)")
    with pytest.raises(ValueError):
        db.execute("INSERT INTO t VALUES (1)")
    with pytest.raises(ValueError):
        db.execute("INSERT INTO t (a, b) VALUES (1, 2, 3)")


# --------------------------------------------------------------------------- #
# Keyword case-insensitivity / identifier case-sensitivity
# --------------------------------------------------------------------------- #
def test_keywords_case_insensitive():
    db = Database()
    db.execute("create table t (id int, name text)")
    db.execute("insert into t values (1, 'a')")
    assert db.execute("select * from t") == [{"id": 1, "name": "a"}]


def test_identifiers_case_sensitive():
    db = Database()
    db.execute("CREATE TABLE T (id INT)")
    with pytest.raises(ValueError):
        db.execute("SELECT * FROM t")  # different table name


# --------------------------------------------------------------------------- #
# Projection
# --------------------------------------------------------------------------- #
def test_select_star_all_columns_in_order():
    db = _people_db()
    rows = db.execute("SELECT * FROM t")
    assert [list(r.keys()) for r in rows][0] == ["id", "name", "score"]


def test_select_column_subset_and_keys():
    db = _people_db()
    rows = db.execute("SELECT name, score FROM t")
    assert rows == [
        {"name": "alice", "score": 10},
        {"name": "bob", "score": None},
        {"name": "cara", "score": 20},
        {"name": "dan", "score": None},
    ]


def test_select_alias_key():
    db = _people_db()
    rows = db.execute("SELECT name AS who FROM t LIMIT 1")
    assert rows == [{"who": "alice"}]


def test_select_unknown_column_raises():
    db = _people_db()
    with pytest.raises(ValueError):
        db.execute("SELECT zzz FROM t")


def test_select_unknown_table_raises():
    db = Database()
    with pytest.raises(ValueError):
        db.execute("SELECT * FROM nope")


# --------------------------------------------------------------------------- #
# WHERE comparisons
# --------------------------------------------------------------------------- #
def test_where_int_comparisons_all_operators():
    db = _people_db()
    ids = lambda sql: [r["id"] for r in db.execute(sql)]
    assert ids("SELECT id FROM t WHERE score = 10") == [1]
    assert ids("SELECT id FROM t WHERE score <> 10") == [3]  # NULLs dropped
    assert ids("SELECT id FROM t WHERE score < 20") == [1]
    assert ids("SELECT id FROM t WHERE score <= 20") == [1, 3]
    assert ids("SELECT id FROM t WHERE score > 10") == [3]
    assert ids("SELECT id FROM t WHERE score >= 10") == [1, 3]


def test_where_literal_on_left_is_normalised():
    db = _people_db()
    # 15 > score  is equivalent to  score < 15
    assert [r["id"] for r in db.execute("SELECT id FROM t WHERE 15 > score")] == [1]


def test_where_string_comparison_lexicographic():
    db = _people_db()
    # names: alice, bob, cara, dan ; > 'bob' lexicographically -> cara, dan
    assert [r["name"] for r in db.execute("SELECT name FROM t WHERE name > 'bob'")] == ["cara", "dan"]


def test_where_type_mismatch_raises():
    db = _people_db()
    with pytest.raises(ValueError):
        db.execute("SELECT id FROM t WHERE score = 'x'")   # INT col vs str
    with pytest.raises(ValueError):
        db.execute("SELECT id FROM t WHERE name = 5")      # TEXT col vs int


# --------------------------------------------------------------------------- #
# Three-valued (Kleene) logic
# --------------------------------------------------------------------------- #
def test_three_valued_equals_drops_null_rows():
    # x = 5 and x <> 5 are both UNKNOWN when x is NULL, so the NULL row drops.
    db = _people_db()
    assert [r["id"] for r in db.execute("SELECT id FROM t WHERE score = 10")] == [1]
    assert [r["id"] for r in db.execute("SELECT id FROM t WHERE score <> 99")] == [1, 3]


def test_three_valued_not_of_unknown_is_unknown():
    # NOT (score > 5): id1 TRUE->FALSE, NULLs UNKNOWN->UNKNOWN(drop), id3 TRUE->FALSE
    db = _people_db()
    assert db.execute("SELECT id FROM t WHERE NOT (score > 5)") == []


def test_three_valued_or_with_true():
    # score > 15 OR score IS NULL: id3 (TRUE) plus the two NULL rows (TRUE via IS NULL)
    db = _people_db()
    assert [r["id"] for r in db.execute(
        "SELECT id FROM t WHERE score > 15 OR score IS NULL")] == [2, 3, 4]


def test_three_valued_and_with_false():
    # score > 100 (FALSE/UNKNOWN) AND score IS NULL -> FALSE for every row
    db = _people_db()
    assert db.execute("SELECT id FROM t WHERE score > 100 AND score IS NULL") == []


def test_three_valued_or_unknown_stays_unknown():
    # score = 99 is UNKNOWN on NULL rows and FALSE elsewhere; OR score = 99 again
    # keeps it non-TRUE, so nothing is kept.
    db = _people_db()
    assert db.execute("SELECT id FROM t WHERE score = 99 OR score = 98") == []


def test_precedence_or_lower_than_and():
    # WHERE score = 10 OR score = 20 AND name = 'zzz'
    #   = score=10 OR (score=20 AND FALSE) = score=10
    db = _people_db()
    assert [r["id"] for r in db.execute(
        "SELECT id FROM t WHERE score = 10 OR score = 20 AND name = 'zzz'")] == [1]


def test_is_null_and_is_not_null():
    db = _people_db()
    assert [r["id"] for r in db.execute("SELECT id FROM t WHERE score IS NULL")] == [2, 4]
    assert [r["id"] for r in db.execute("SELECT id FROM t WHERE score IS NOT NULL")] == [1, 3]


# --------------------------------------------------------------------------- #
# GROUP BY + aggregates
# --------------------------------------------------------------------------- #
def test_group_by_count_star_and_count_col():
    db = _group_db()
    rows = db.execute("SELECT g, COUNT(*), COUNT(v) FROM s GROUP BY g ORDER BY g")
    assert rows == [
        {"g": "a", "COUNT(*)": 3, "COUNT(v)": 2},   # a has 3 rows, 2 non-null v
        {"g": "b", "COUNT(*)": 1, "COUNT(v)": 1},
        {"g": "c", "COUNT(*)": 1, "COUNT(v)": 0},   # c's only v is NULL
    ]


def test_group_by_sum_and_avg_ignore_nulls():
    db = _group_db()
    rows = db.execute("SELECT g, SUM(v), AVG(v) FROM s GROUP BY g ORDER BY g")
    assert rows[0]["g"] == "a" and rows[0]["SUM(v)"] == 4
    assert gu.close(rows[0]["AVG(v)"], 2.0)
    assert isinstance(rows[0]["AVG(v)"], float)
    assert rows[1] == {"g": "b", "SUM(v)": 5, "AVG(v)": 5.0}
    # group c: only NULL values -> SUM and AVG are NULL
    assert rows[2]["g"] == "c"
    assert rows[2]["SUM(v)"] is None
    assert rows[2]["AVG(v)"] is None


def test_group_by_min_max_ignore_nulls():
    db = _group_db()
    rows = db.execute("SELECT g, MIN(v), MAX(v) FROM s GROUP BY g ORDER BY g")
    assert rows[0] == {"g": "a", "MIN(v)": 1, "MAX(v)": 3}
    assert rows[1] == {"g": "b", "MIN(v)": 5, "MAX(v)": 5}
    assert rows[2] == {"g": "c", "MIN(v)": None, "MAX(v)": None}


def test_group_by_null_forms_own_group():
    # Isolates grouping (NULL is its own group, two NULLs are the same group);
    # order-insensitive so it does not depend on the NULL-ordering rule.
    db = Database()
    db.execute("CREATE TABLE g2 (k TEXT, v INT)")
    db.execute("INSERT INTO g2 VALUES (NULL, 1)")
    db.execute("INSERT INTO g2 VALUES (NULL, 2)")
    db.execute("INSERT INTO g2 VALUES ('x', 9)")
    rows = db.execute("SELECT k, COUNT(*), SUM(v) FROM g2 GROUP BY k")
    by_key = {r["k"]: (r["COUNT(*)"], r["SUM(v)"]) for r in rows}
    assert len(rows) == 2  # exactly two groups: NULL and 'x'
    assert by_key[None] == (2, 3)   # the two NULL rows merge into one group
    assert by_key["x"] == (1, 9)


def test_group_by_validation_error_for_bare_column():
    # v is neither grouped nor aggregated -> ValueError
    db = _group_db()
    with pytest.raises(ValueError):
        db.execute("SELECT g, v FROM s GROUP BY g")


def test_group_by_alias():
    db = _group_db()
    rows = db.execute("SELECT g, COUNT(*) AS n FROM s GROUP BY g ORDER BY g")
    assert rows == [{"g": "a", "n": 3}, {"g": "b", "n": 1}, {"g": "c", "n": 1}]


def test_aggregate_without_group_by_whole_table():
    db = _group_db()  # v values: 1, 3, NULL, 5, NULL -> non-null {1,3,5}
    rows = db.execute("SELECT COUNT(*), COUNT(v), SUM(v), MIN(v), MAX(v) FROM s")
    assert len(rows) == 1
    assert rows[0]["COUNT(*)"] == 5
    assert rows[0]["COUNT(v)"] == 3
    assert rows[0]["SUM(v)"] == 9
    assert rows[0]["MIN(v)"] == 1
    assert rows[0]["MAX(v)"] == 5


def test_aggregate_avg_without_group_by_is_float():
    db = _group_db()
    rows = db.execute("SELECT AVG(v) FROM s")
    assert len(rows) == 1
    assert gu.close(rows[0]["AVG(v)"], 3.0)  # (1+3+5)/3
    assert isinstance(rows[0]["AVG(v)"], float)


def test_aggregate_over_empty_table_one_row():
    db = Database()
    db.execute("CREATE TABLE e (v INT)")
    rows = db.execute("SELECT COUNT(*), SUM(v), AVG(v), MIN(v), MAX(v) FROM e")
    assert rows == [{"COUNT(*)": 0, "SUM(v)": None, "AVG(v)": None,
                     "MIN(v)": None, "MAX(v)": None}]


def test_count_col_key_spelling():
    db = _group_db()
    rows = db.execute("SELECT COUNT(*), SUM(v) FROM s")
    # default result keys use the exact canonical spelling
    assert set(rows[0].keys()) == {"COUNT(*)", "SUM(v)"}


def test_star_with_aggregate_or_group_raises():
    db = _group_db()
    with pytest.raises(ValueError):
        db.execute("SELECT * FROM s GROUP BY g")


# --------------------------------------------------------------------------- #
# ORDER BY
# --------------------------------------------------------------------------- #
def test_order_by_asc_default():
    db = _people_db()
    rows = db.execute("SELECT id FROM t WHERE score IS NOT NULL ORDER BY score")
    assert [r["id"] for r in rows] == [1, 3]  # 10 < 20


def test_order_by_multi_key_stable():
    db = Database()
    db.execute("CREATE TABLE m (a INT, b INT, id INT)")
    for a, b, i in [(1, 2, 10), (1, 1, 11), (2, 1, 12), (1, 2, 13)]:
        db.execute(f"INSERT INTO m VALUES ({a}, {b}, {i})")
    rows = db.execute("SELECT id FROM m ORDER BY a ASC, b DESC")
    # a ASC, then b DESC; (1,2) block stable -> 10 before 13.
    assert [r["id"] for r in rows] == [10, 13, 11, 12]


def test_order_by_column_not_in_select_list():
    db = Database()
    db.execute("CREATE TABLE m (a INT, id INT)")
    for a, i in [(3, 1), (1, 2), (2, 3)]:
        db.execute(f"INSERT INTO m VALUES ({a}, {i})")
    rows = db.execute("SELECT id FROM m ORDER BY a DESC")
    assert [r["id"] for r in rows] == [1, 3, 2]  # a = 3,2,1


def test_order_by_unknown_column_raises():
    db = _people_db()
    with pytest.raises(ValueError):
        db.execute("SELECT id FROM t ORDER BY zzz")


# --- FAIL_TO_PASS: NULL ordering (kills the planted defect) ----------------
def test_order_by_asc_nulls_first():  # [FAIL_TO_PASS]
    db = _people_db()
    rows = db.execute("SELECT id, score FROM t ORDER BY score ASC")
    # NULLs first under ASC; the two NULL rows keep insertion order (2 before 4).
    assert [(r["id"], r["score"]) for r in rows] == [
        (2, None), (4, None), (1, 10), (3, 20),
    ]


def test_order_by_desc_nulls_last():  # [FAIL_TO_PASS]
    db = _people_db()
    rows = db.execute("SELECT id, score FROM t ORDER BY score DESC")
    # NULLs last under DESC; non-null values descending (20, 10).
    assert [(r["id"], r["score"]) for r in rows] == [
        (3, 20), (1, 10), (2, None), (4, None),
    ]


def test_order_by_multikey_null_ordering():  # [FAIL_TO_PASS]
    # First key non-null everywhere; second key has NULLs that must sort first
    # under ASC within each first-key group.
    db = Database()
    db.execute("CREATE TABLE m (a INT, b INT, id INT)")
    for a, b, i in [(1, 5, 10), (1, None, 11), (1, 2, 12), (2, None, 13), (2, 7, 14)]:
        bv = "NULL" if b is None else str(b)
        db.execute(f"INSERT INTO m VALUES ({a}, {bv}, {i})")
    rows = db.execute("SELECT id FROM m ORDER BY a ASC, b ASC")
    # a=1: b NULL(11) first, then 2(12), then 5(10); a=2: NULL(13) then 7(14)
    assert [r["id"] for r in rows] == [11, 12, 10, 13, 14]


def test_order_by_all_nulls_then_limit():  # [FAIL_TO_PASS]
    # Mixed NULL/non-null with LIMIT after ordering: ASC NULLs-first means the
    # first two rows are the NULL rows. The broken (NULLs-last) variant returns
    # the non-null rows instead.
    db = Database()
    db.execute("CREATE TABLE t2 (id INT, s INT)")
    for i, s in [(1, 100), (2, None), (3, 50), (4, None)]:
        sv = "NULL" if s is None else str(s)
        db.execute(f"INSERT INTO t2 VALUES ({i}, {sv})")
    rows = db.execute("SELECT id FROM t2 ORDER BY s ASC LIMIT 2")
    assert [r["id"] for r in rows] == [2, 4]  # the two NULL rows, in insertion order


# --------------------------------------------------------------------------- #
# LIMIT / OFFSET
# --------------------------------------------------------------------------- #
def test_limit_and_offset_after_ordering():
    db = _people_db()
    rows = db.execute("SELECT id FROM t ORDER BY id LIMIT 2 OFFSET 1")
    assert [r["id"] for r in rows] == [2, 3]


def test_limit_zero_returns_empty():
    db = _people_db()
    assert db.execute("SELECT id FROM t LIMIT 0") == []


def test_offset_past_end_returns_empty():
    db = _people_db()
    assert db.execute("SELECT id FROM t ORDER BY id OFFSET 100") == []


def test_negative_limit_or_offset_raises():
    db = _people_db()
    with pytest.raises(ValueError):
        db.execute("SELECT id FROM t LIMIT -1")
    with pytest.raises(ValueError):
        db.execute("SELECT id FROM t OFFSET -5")


# --------------------------------------------------------------------------- #
# DISTINCT
# --------------------------------------------------------------------------- #
def test_distinct_with_nulls():
    # Isolates DISTINCT dedup with NULL==NULL; order-insensitive so it does not
    # depend on the NULL-ordering rule.
    db = Database()
    db.execute("CREATE TABLE d (a INT, b TEXT)")
    for a, b in [(1, "x"), (1, "x"), (None, "y"), (None, "y"), (2, None), (2, None)]:
        av = "NULL" if a is None else str(a)
        bv = "NULL" if b is None else f"'{b}'"
        db.execute(f"INSERT INTO d VALUES ({av}, {bv})")
    rows = db.execute("SELECT DISTINCT a, b FROM d")
    pairs = {(r["a"], r["b"]) for r in rows}
    # Each of (1,'x'), (None,'y'), (2,None) collapses to exactly one row.
    assert len(rows) == 3
    assert pairs == {(1, "x"), (None, "y"), (2, None)}


def test_distinct_applies_before_limit():
    db = Database()
    db.execute("CREATE TABLE d (a INT)")
    for a in [1, 1, 2, 2, 3]:
        db.execute(f"INSERT INTO d VALUES ({a})")
    rows = db.execute("SELECT DISTINCT a FROM d ORDER BY a LIMIT 2")
    assert [r["a"] for r in rows] == [1, 2]


# --------------------------------------------------------------------------- #
# Malformed statements
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sql", [
    "SELECT FROM t",                 # empty select-list
    "SELECT * t",                    # missing FROM
    "SELEC * FROM t",                # misspelled keyword -> identifier in stmt position
    "CREATE TABLE t (id INTEGER)",   # unsupported type keyword
    "INSERT INTO t VALUES (1",       # unbalanced parens
    "SELECT * FROM t WHERE",         # dangling WHERE
    "SELECT * FROM t ORDER score",   # ORDER without BY
    "SELECT * FROM t GROUP g",       # GROUP without BY
    "DROP TABLE t",                  # unsupported statement
    "SELECT * FROM t WHERE score = ", # incomplete comparison
])
def test_malformed_statements_raise_valueerror(sql):
    db = Database()
    db.execute("CREATE TABLE t (id INT, name TEXT, score INT)")
    db.execute("INSERT INTO t VALUES (1, 'a', 5)")
    with pytest.raises(ValueError):
        db.execute(sql)


def test_select_does_not_mutate_table():
    db = _people_db()
    before = db.execute("SELECT * FROM t")
    db.execute("SELECT id FROM t WHERE score > 5 ORDER BY score DESC LIMIT 1")
    after = db.execute("SELECT * FROM t")
    assert before == after


# --------------------------------------------------------------------------- #
# Advisory: code quality (never asserted as pass/fail)
# --------------------------------------------------------------------------- #
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
