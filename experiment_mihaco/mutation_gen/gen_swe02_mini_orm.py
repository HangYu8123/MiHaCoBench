"""Generate the oracle-grounded mutation corpus for swe_bench/swe02_mini_orm.

Independent oracle: naive Python filter/sort/slice — a structurally-different
brute-force that does NOT share code with the gold (no Database/Query classes,
just plain list comprehensions and built-in sort).

The task's bug: chaining two or more .where() conditions only keeps the LAST
predicate instead of ANDing all of them. The corpus is seeded with inputs that
require the full AND of multiple predicates to be evaluated correctly, so any
correct-but-wrong implementation (the __broken variant, mutants of query.py,
and hand-written common-mistake implementations) is killed.

Provenance: Query builder AND-composition — cf. SQLAlchemy issue #5723.
Grader ground truth: independent naive filter.

Run:  python3 experiment_mihaco/mutation_gen/gen_swe02_mini_orm.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "swe_bench", "swe02_mini_orm"
GOLD_DIR = gu.GOLD_ROOT / CATEGORY / TASK_ID
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / f"{TASK_ID}__broken"

# Load source text of the three modules (gold)
_DB_SRC     = (GOLD_DIR / "db.py").read_text()
_PRED_SRC   = (GOLD_DIR / "predicates.py").read_text()
_QUERY_SRC  = (GOLD_DIR / "query.py").read_text()

# Load source text of __broken modules
_QUERY_BROKEN_SRC = (BROKEN_DIR / "query.py").read_text()
_DB_BROKEN_SRC    = (BROKEN_DIR / "db.py").read_text()
_PRED_BROKEN_SRC  = (BROKEN_DIR / "predicates.py").read_text()


# ---------------------------------------------------------------------------
# Pure function wrapper: run_query(rows, wheres, order, descending, limit)
# using the gold package.
# ---------------------------------------------------------------------------
def _make_run_query(db_src: str, pred_src: str, query_src: str):
    """Create a run_query function that uses a package from the given sources."""
    pkg_files = {
        "db.py":         db_src,
        "predicates.py": pred_src,
        "query.py":      query_src,
    }
    Database = ms.load_callable_from_package(pkg_files, "db.py", "Database")

    def run_query(rows, wheres, order, descending, limit):
        """Pure wrapper: build a fresh Database+Query, apply filters, return rows."""
        db = Database(list(rows))
        q = db.query()
        for (field, op, value) in wheres:
            q = q.where(field, op, value)
        if order is not None:
            q = q.order_by(order, descending=descending)
        if limit is not None:
            q = q.limit(limit)
        return db.run(q)

    return run_query


# Gold callable
gold = _make_run_query(_DB_SRC, _PRED_SRC, _QUERY_SRC)


# ---------------------------------------------------------------------------
# Independent oracle: naive Python (no Database/Query classes)
# ---------------------------------------------------------------------------
def _match(row: dict, field: str, op: str, value) -> bool:
    if op == "eq":
        return row[field] == value
    elif op == "gt":
        return row[field] > value
    elif op == "lt":
        return row[field] < value
    raise ValueError(f"Unknown op: {op!r}")


def oracle(rows, wheres, order, descending, limit):
    """Independent brute-force oracle: plain list comprehension + sort + slice."""
    filtered = [r for r in rows if all(_match(r, f, op, v) for (f, op, v) in wheres)]
    if order is not None:
        filtered = sorted(filtered, key=lambda r: r[order], reverse=descending)
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


# ---------------------------------------------------------------------------
# Wrong implementations
# ---------------------------------------------------------------------------

# Hand-written: only-last-predicate (the __broken pattern reimplemented)
_ONLY_LAST_PREDICATE = '''\
def run_query(rows, wheres, order, descending, limit):
    """BUG: only applies the last where predicate, ignores earlier ones."""
    filtered = list(rows)
    if wheres:
        field, op, value = wheres[-1]
        if op == "eq":
            filtered = [r for r in filtered if r[field] == value]
        elif op == "gt":
            filtered = [r for r in filtered if r[field] > value]
        elif op == "lt":
            filtered = [r for r in filtered if r[field] < value]
    if order is not None:
        filtered = sorted(filtered, key=lambda r: r[order], reverse=descending)
    if limit is not None:
        filtered = filtered[:limit]
    return filtered
'''

# Hand-written: OR instead of AND (any predicate matches -> include)
_OR_INSTEAD_OF_AND = '''\
def run_query(rows, wheres, order, descending, limit):
    """BUG: uses OR instead of AND for combining where clauses."""
    def _match(row, field, op, value):
        if op == "eq": return row[field] == value
        if op == "gt": return row[field] > value
        if op == "lt": return row[field] < value
        return False
    if wheres:
        filtered = [r for r in rows if any(_match(r, f, op, v) for (f, op, v) in wheres)]
    else:
        filtered = list(rows)
    if order is not None:
        filtered = sorted(filtered, key=lambda r: r[order], reverse=descending)
    if limit is not None:
        filtered = filtered[:limit]
    return filtered
'''

# Hand-written: order_by ignores descending (always ascending)
_ORDER_IGNORES_DESCENDING = '''\
def run_query(rows, wheres, order, descending, limit):
    """BUG: order_by always sorts ascending, ignores descending flag."""
    def _match(row, field, op, value):
        if op == "eq": return row[field] == value
        if op == "gt": return row[field] > value
        if op == "lt": return row[field] < value
        return False
    filtered = [r for r in rows if all(_match(r, f, op, v) for (f, op, v) in wheres)]
    if order is not None:
        filtered = sorted(filtered, key=lambda r: r[order])  # BUG: always ascending
    if limit is not None:
        filtered = filtered[:limit]
    return filtered
'''

# Hand-written: limit off-by-one (returns n+1 rows)
_LIMIT_OFF_BY_ONE = '''\
def run_query(rows, wheres, order, descending, limit):
    """BUG: limit returns n+1 rows instead of n."""
    def _match(row, field, op, value):
        if op == "eq": return row[field] == value
        if op == "gt": return row[field] > value
        if op == "lt": return row[field] < value
        return False
    filtered = [r for r in rows if all(_match(r, f, op, v) for (f, op, v) in wheres)]
    if order is not None:
        filtered = sorted(filtered, key=lambda r: r[order], reverse=descending)
    if limit is not None:
        filtered = filtered[:limit + 1]  # BUG: off-by-one
    return filtered
'''


def _wrong_fns():
    wrongs = []

    # 1. The real __broken variant
    try:
        broken_run_query = _make_run_query(_DB_BROKEN_SRC, _PRED_BROKEN_SRC, _QUERY_BROKEN_SRC)
        wrongs.append(("__broken", broken_run_query))
    except Exception as e:
        print(f"Warning: could not load __broken: {e}")

    # 2. Hand-written common-mistake wrong solutions
    for label, src in [
        ("only_last_predicate",    _ONLY_LAST_PREDICATE),
        ("or_instead_of_and",      _OR_INSTEAD_OF_AND),
        ("order_ignores_descending", _ORDER_IGNORES_DESCENDING),
        ("limit_off_by_one",       _LIMIT_OFF_BY_ONE),
    ]:
        try:
            fn = ms.load_callable_from_source(src, "run_query")
            wrongs.append((label, fn))
        except Exception as e:
            print(f"Warning: could not load hand-written wrong {label!r}: {e}")

    # 3. AST mutants of query.py (the buggy module — same as __broken)
    # We mutate query.py and reload the full package with the mutated version.
    for label, mutant_query in ms.generate_mutants(_QUERY_SRC):
        try:
            fn = _make_run_query(_DB_SRC, _PRED_SRC, mutant_query)
            wrongs.append((f"query_mut_{label}", fn))
        except Exception:
            continue

    # 4. AST mutants of predicates.py
    for label, mutant_pred in ms.generate_mutants(_PRED_SRC):
        try:
            fn = _make_run_query(_DB_SRC, mutant_pred, _QUERY_SRC)
            wrongs.append((f"pred_mut_{label}", fn))
        except Exception:
            continue

    return wrongs


# ---------------------------------------------------------------------------
# Input generator
# ---------------------------------------------------------------------------
_RNG = random.Random(20260616)

_STR_FIELDS = ["dept", "name", "team", "role"]
_INT_FIELDS = ["age", "score", "level", "rank"]
_DEPTS  = ["eng", "mktg", "hr", "ops", "fin"]
_NAMES  = ["alice", "bob", "carol", "dave", "eve", "frank", "grace", "hank"]
_TEAMS  = ["alpha", "beta", "gamma"]
_ROLES  = ["dev", "mgr", "qa", "sre"]
_OPS    = ["eq", "gt", "lt"]


def _rand_row() -> dict:
    row = {
        "dept":  _RNG.choice(_DEPTS),
        "name":  _RNG.choice(_NAMES),
        "team":  _RNG.choice(_TEAMS),
        "role":  _RNG.choice(_ROLES),
        "age":   _RNG.randint(20, 50),
        "score": _RNG.randint(50, 100),
        "level": _RNG.randint(1, 10),
        "rank":  _RNG.randint(1, 20),
    }
    return row


def _rand_where_clause(rows: list[dict]) -> tuple:
    """Generate a (field, op, value) predicate that is meaningful given the rows."""
    op = _RNG.choice(_OPS)
    if _RNG.random() < 0.5 and _STR_FIELDS:
        field = _RNG.choice(_STR_FIELDS)
        op = "eq"   # only eq makes sense for str fields
        values = [r[field] for r in rows]
        value = _RNG.choice(values) if values else _RNG.choice(_DEPTS)
    else:
        field = _RNG.choice(_INT_FIELDS)
        values = sorted(set(r[field] for r in rows))
        if values:
            # pick a threshold in the middle range so we get both sides
            mid = values[len(values) // 2]
            value = mid + _RNG.randint(-3, 3)
        else:
            value = _RNG.randint(20, 80)
    return (field, op, value)


def _inputs():
    out = []

    # --- Random small/medium cases ---
    for _ in range(1500):
        n_rows = _RNG.randint(1, 8)
        rows = [_rand_row() for _ in range(n_rows)]
        n_wheres = _RNG.randint(0, 3)
        wheres = [_rand_where_clause(rows) for _ in range(n_wheres)]
        order = _RNG.choice([None, None, "age", "score", "level", "rank", "dept"])
        descending = _RNG.choice([True, False])
        if order is None:
            descending = False
        limit_choices = [None, None, 1, 2, 3, 5, 10]
        limit = _RNG.choice(limit_choices)
        out.append((rows, wheres, order, descending, limit))

    # --- Explicit high-value cases (AND-composition discriminators) ---

    ROWS = [
        {"name": "alice",  "age": 30, "score": 85, "dept": "eng",  "level": 3},
        {"name": "bob",    "age": 25, "score": 72, "dept": "eng",  "level": 2},
        {"name": "carol",  "age": 35, "score": 91, "dept": "mktg", "level": 4},
        {"name": "dave",   "age": 28, "score": 72, "dept": "eng",  "level": 2},
        {"name": "eve",    "age": 40, "score": 68, "dept": "mktg", "level": 5},
        {"name": "frank",  "age": 25, "score": 95, "dept": "eng",  "level": 1},
    ]

    # AND of 2 — returns intersection (not last-predicate only)
    out.append((ROWS, [("dept", "eq", "eng"), ("age", "gt", 26)], None, False, None))

    # AND of 3 — all three must hold simultaneously
    out.append((ROWS, [("dept", "eq", "eng"), ("age", "gt", 24), ("score", "gt", 80)], None, False, None))

    # AND yields empty (contradictory conditions)
    out.append((ROWS, [("age", "gt", 35), ("age", "lt", 25)], None, False, None))

    # AND + order_by descending
    out.append((ROWS, [("dept", "eq", "eng"), ("score", "gt", 70)], "score", True, None))

    # Single where (pass-to-pass)
    out.append((ROWS, [("dept", "eq", "eng")], None, False, None))

    # Select all (no where)
    out.append((ROWS, [], None, False, None))

    # Order by ascending
    out.append((ROWS, [], "age", False, None))

    # Order by descending
    out.append((ROWS, [], "score", True, None))

    # Limit only
    out.append((ROWS, [], None, False, 2))

    # AND + limit
    out.append((ROWS, [("dept", "eq", "eng"), ("age", "gt", 24)], "score", True, 3))

    # Empty rows
    out.append(([], [("age", "gt", 20)], None, False, None))

    # Single row
    out.append(([{"age": 30, "score": 80, "dept": "eng", "level": 2}],
                [("age", "gt", 25), ("score", "gt", 75)], None, False, None))

    # AND that has no row surviving all conditions
    out.append((ROWS, [("dept", "eq", "eng"), ("dept", "eq", "mktg")], None, False, None))

    # Three-field AND, complex
    out.append((ROWS, [("dept", "eq", "mktg"), ("age", "gt", 30), ("score", "gt", 85)],
                "age", False, None))

    # Limit > number of matching rows
    out.append((ROWS, [("dept", "eq", "mktg")], "score", True, 10))

    # Limit = 1 from multi-row result
    out.append((ROWS, [("dept", "eq", "eng")], "score", True, 1))

    return out


def main() -> int:
    wrongs = _wrong_fns()
    print(f"Total wrong solutions: {len(wrongs)}")
    inputs = _inputs()
    print(f"Total inputs: {len(inputs)}")
    corpus = ms.build_corpus(gold, oracle, wrongs, inputs, max_keep=120)
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "independent-reference: naive Python filter (list comprehension + sorted + slice)",
        "provenance": (
            "Query builder AND-composition: multiple WHERE conditions composed incorrectly "
            "— cf. SQLAlchemy issue #5723. Grader ground truth: independent naive filter."
        ),
        "input_seed": 20260616,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
