"""Grader for long_horizon/lh13_quota_ledger.

Runs the candidate's 10-step CLI chain, verifies the provenance link at each step,
and compares each step's output to the canonical fixture in expected/steps.json.
The candidate's own step output is fed forward so an early error cascades. One
parametrised test per step plus a final cumulative reconciliation test.

Validity invariant: PASSES on the gold reference, FAILS on the broken reference
(which re-derives the grant from the full budget instead of the running remainder,
so the running `remaining` diverges from step 3 onward and reconciliation fails).
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh13_quota_ledger"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 10


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh13")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursive approximate comparison: dicts, lists, scalars."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            return False
        return all(_approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, bool):
        return a == b
    try:
        return gu.close(float(a), float(b), rtol=1e-3, atol=1e-6)
    except (TypeError, ValueError):
        return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], f"step {k} did not run successfully: {chain}"
    assert rec["prov_ok"], f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), (
        f"step {k} data mismatch.\n  got: {rec['data']}\n  want: {EXPECTED[str(k)]['data']}"
    )


def test_final_cumulative(chain):
    """All steps ran and the final reconciliation matches the conserved ledger."""
    assert len(chain) == N_STEPS, f"chain terminated early after {len(chain)} steps"
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (step 10) did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step 10 data should be a dict, got {type(d)}"
    # Budget 100 fully consumed: r1-r4 fully (30+25+20+15=90), r5 partial (10 of 40),
    # r6-r8 rejected. total_granted=100, remaining=0, utilization=1.0, reconciled.
    assert gu.close(float(d["total_granted"]), 100.0, rtol=1e-3), f"total_granted: {d['total_granted']}"
    assert gu.close(float(d["remaining"]), 0.0, atol=1e-6), f"remaining: {d['remaining']}"
    assert gu.close(float(d["utilization"]), 1.0, rtol=1e-3), f"utilization: {d['utilization']}"
    assert d["fully_granted"] == 4, f"fully_granted: {d['fully_granted']}"
    assert d["partial"] == 1, f"partial: {d['partial']}"
    assert d["rejected"] == 3, f"rejected: {d['rejected']}"
    assert d["reconciled"] is True, "ledger did not reconcile (total_granted + remaining != budget)"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
