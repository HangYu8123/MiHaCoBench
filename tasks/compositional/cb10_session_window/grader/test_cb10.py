"""Grader for compositional/cb10_session_window. Public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Ground truth is an INDEPENDENT pure-Python reference (``_ref``) applying the
correct INCLUSIVE rule (continue while ``ts - prev_ts <= gap``). The broken
reference uses ``>= gap`` and therefore splits sessions at exact-gap boundaries;
the exact-gap and random-partition tests catch it, while single-event, far-apart,
and exception-path tests still pass on the broken variant.
"""
from __future__ import annotations

import random

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb10_session_window"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
sessionize = gu.load_callable(SOL, "solution.py", "sessionize")


# ---------------------------------------------------------------------------
# Independent reference: correct inclusive-gap sessionization (pure Python).
# ---------------------------------------------------------------------------

def _ref(rows: list[tuple], gap: float) -> list[dict]:
    """rows = list of (ts, id). Returns the canonical session list."""
    ordered = sorted(rows, key=lambda r: (r[0], r[1]))
    sessions: list[dict] = []
    prev_ts = None
    for ts, i in ordered:
        if sessions and (ts - prev_ts) <= gap:
            s = sessions[-1]
            s["ids"].append(i)
            s["end_ts"] = ts
            s["count"] += 1
        else:
            sessions.append({"ids": [i], "start_ts": ts, "end_ts": ts, "count": 1})
        prev_ts = ts
    return sessions


def _norm(sessions: list[dict]) -> list[tuple]:
    """Comparable normal form: (tuple(ids), start_ts, end_ts, count) per session."""
    return [(tuple(s["ids"]), s["start_ts"], s["end_ts"], s["count"]) for s in sessions]


# ---------------------------------------------------------------------------
# 1. Single event -> one session.
# ---------------------------------------------------------------------------

def test_single_event():
    df = pd.DataFrame({"id": [7], "ts": [3]})
    out = sessionize(df, 5)
    assert _norm(out) == [((7,), 3, 3, 1)]


# ---------------------------------------------------------------------------
# 2. Empty df -> [].
# ---------------------------------------------------------------------------

def test_empty_df():
    df = pd.DataFrame({"id": [], "ts": []})
    assert sessionize(df, 5) == []


# ---------------------------------------------------------------------------
# 3. Worked example from TASK.md.
# ---------------------------------------------------------------------------

def test_worked_example():
    df = pd.DataFrame({"id": [1, 2, 3, 4], "ts": [0, 5, 10, 20]})
    out = sessionize(df, 5)
    assert _norm(out) == [((1, 2, 3), 0, 10, 3), ((4,), 20, 20, 1)]


# ---------------------------------------------------------------------------
# 4. Exact-gap boundary JOINS (the discriminator vs the broken >= variant).
# ---------------------------------------------------------------------------

def test_exact_gap_joins():
    # Every consecutive gap is exactly 5 -> a single session under the inclusive rule.
    df = pd.DataFrame({"id": [1, 2, 3, 4, 5], "ts": [0, 5, 10, 15, 20]})
    out = sessionize(df, 5)
    assert _norm(out) == [((1, 2, 3, 4, 5), 0, 20, 5)]


# ---------------------------------------------------------------------------
# 5. Strictly-greater gap splits.
# ---------------------------------------------------------------------------

def test_strict_gap_splits():
    df = pd.DataFrame({"id": [1, 2, 3], "ts": [0, 6, 12]})  # gaps of 6 > 5
    out = sessionize(df, 5)
    assert _norm(out) == [((1,), 0, 0, 1), ((2,), 6, 6, 1), ((3,), 12, 12, 1)]


# ---------------------------------------------------------------------------
# 6. Tie-break on id when timestamps are equal.
# ---------------------------------------------------------------------------

def test_tie_break_on_id():
    # Same ts -> ordered by id; gap 0 keeps them together (0 <= gap).
    df = pd.DataFrame({"id": [9, 2, 5], "ts": [4, 4, 4]})
    out = sessionize(df, 0)
    assert _norm(out) == [((2, 5, 9), 4, 4, 3)]


# ---------------------------------------------------------------------------
# 7. Unsorted input must be sorted before sessionizing.
# ---------------------------------------------------------------------------

def test_unsorted_input():
    df = pd.DataFrame({"id": [4, 1, 3, 2], "ts": [20, 0, 10, 5]})
    out = sessionize(df, 5)
    assert _norm(out) == _norm(_ref(list(zip(df["ts"], df["id"])), 5))


# ---------------------------------------------------------------------------
# 8. Full partition property on many random inputs vs the reference.
# ---------------------------------------------------------------------------

def test_random_partition_vs_ref():
    rng = random.Random(2026)
    for _ in range(300):
        n = rng.randint(1, 20)
        ids = rng.sample(range(1, 1000), n)
        # Timestamps with many exact-gap boundaries to stress the > vs >= rule.
        ts = sorted(rng.randint(0, 60) for _ in range(n))
        rows = list(zip(ts, ids))
        rng.shuffle(rows)
        df = pd.DataFrame({"id": [r[1] for r in rows], "ts": [r[0] for r in rows]})
        gap = rng.randint(0, 10)
        out = sessionize(df, gap)
        assert _norm(out) == _norm(_ref(rows, gap)), f"rows={rows} gap={gap}"
        # Partition invariants.
        all_ids = [i for s in out for i in s["ids"]]
        assert sorted(all_ids) == sorted(ids)
        assert all(s["count"] == len(s["ids"]) >= 1 for s in out)


# ---------------------------------------------------------------------------
# 9. Exception / boundary contract.
# ---------------------------------------------------------------------------

def test_exceptions():
    df = pd.DataFrame({"id": [1, 2], "ts": [0, 1]})
    with pytest.raises(ValueError):
        sessionize(df, -1)
    with pytest.raises(KeyError):
        sessionize(pd.DataFrame({"ts": [0, 1]}), 5)      # missing id
    with pytest.raises(KeyError):
        sessionize(pd.DataFrame({"id": [1, 2]}), 5)      # missing ts


# ---------------------------------------------------------------------------
# 10. Surface form: pandas + numpy used.
# ---------------------------------------------------------------------------

def test_source_uses_libs():
    used = gu.source_uses(SOL, ["pandas", "numpy"])
    assert used["pandas"], "solution must use pandas"
    assert used["numpy"], "solution must use numpy"


# ---------------------------------------------------------------------------
# 11. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
