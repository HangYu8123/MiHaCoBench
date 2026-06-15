"""Grader for long_horizon/lh05_signal_chain.

Runs the candidate's 10-step CLI chain, verifies the provenance link at each
step, and compares each step's output to the canonical fixture in
expected/steps.json. The candidate's own step output is fed forward so an
early error cascades. One parametrised test per step plus a final cumulative
test; the runner's partial score tracks how far the chain stayed correct.

Validity invariant: PASSES on the gold reference, FAILS on the broken reference
(step 5 uses window=2 instead of 3).
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh05_signal_chain"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 10


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh05")
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
    try:
        return gu.close(float(a), float(b), rtol=1e-3)
    except (TypeError, ValueError):
        return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], \
        f"step {k} did not run successfully: {chain}"
    assert rec["prov_ok"], \
        f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), \
        f"step {k} data mismatch.\n  got: {rec['data']}\n  want: {EXPECTED[str(k)]['data']}"


def test_final_cumulative(chain):
    """All steps ran and the final aggregate is correct."""
    assert len(chain) == N_STEPS, \
        f"chain terminated early after {len(chain)} steps"
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (step 10) did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step 10 data should be a dict, got {type(d)}"
    assert gu.close(float(d["sum"]), 2968.75, rtol=1e-3), \
        f"step 10 sum wrong: {d['sum']}"
    assert gu.close(float(d["mean"]), 329.8611111111111, rtol=1e-3), \
        f"step 10 mean wrong: {d['mean']}"
    assert gu.close(float(d["min"]), 0.0, rtol=1e-3, atol=1e-6), \
        f"step 10 min wrong: {d['min']}"
    assert gu.close(float(d["max"]), 1736.1111111111113, rtol=1e-3), \
        f"step 10 max wrong: {d['max']}"
    assert d["count"] == 9, f"step 10 count should be 9, got {d['count']}"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
