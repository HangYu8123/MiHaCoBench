"""Grader for long_horizon/lh04_ledger_roll (8-step pipeline).

Runs the candidate's CLI step chain, verifies the provenance link at each step,
and compares each step's output to the canonical fixture stored in
``expected/steps.json``.  The candidate's own step K output is fed into step K+1,
so an early error cascades automatically.  One test per step plus a final
cumulative test; the runner's partial score tracks how far the chain stayed correct.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh04_ledger_roll"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 8


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh04")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursively compare with float tolerance."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            return False
        return all(_approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, (int, float)):
        if a is None:
            return False
        return gu.close(float(a), float(b))
    return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    """Each step must run, pass the provenance check, and match the expected data."""
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], \
        f"step {k} did not run successfully: {chain}"
    assert rec["prov_ok"], \
        f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), \
        f"step {k} data mismatch.\n  got:      {rec['data']}\n  expected: {EXPECTED[str(k)]['data']}"


def test_final_cumulative(chain):
    """Final step (step 8) must produce the correct aggregate values."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], \
        f"final step (step {N_STEPS}) missing or did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step {N_STEPS} data should be a dict, got {type(d)}"
    assert gu.close(d["sum"], 370.0), f"sum wrong: {d['sum']}"
    assert gu.close(d["mean"], 92.5), f"mean wrong: {d['mean']}"
    assert d["count"] == 4, f"count wrong: {d['count']}"
    assert gu.close(d["min"], 0.0), f"min wrong: {d['min']}"
    assert gu.close(d["max"], 230.0), f"max wrong: {d['max']}"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
