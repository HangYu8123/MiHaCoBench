"""Grader for long_horizon/lh08_token_pipeline.

Runs the candidate's CLI step chain, verifies the provenance link at each step,
and compares each step's output to the canonical fixture stored in expected/steps.json.
The candidate's own step output is fed forward, so an early error cascades. One
test per step plus a final cumulative test; the runner's partial score tracks how
far the chain stayed correct.

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh08_token_pipeline"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 16


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh08")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b) -> bool:
    """Recursively compare two values with float tolerance."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list):
            return False
        return len(a) == len(b) and all(_approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, (int, float)):
        if a is None:
            return False
        return gu.close(float(a), float(b), rtol=1e-4)
    return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    """Each step must run, pass provenance check, and produce the expected data."""
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], (
        f"step {k} did not run: chain so far = {chain}"
    )
    assert rec["prov_ok"], (
        f"step {k} provenance does not match the consumed artifact"
    )
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), (
        f"step {k} data mismatch.\n  got:      {rec['data']}\n  expected: {EXPECTED[str(k)]['data']}"
    )


def test_final_cumulative(chain):
    """Final step must produce the correct aggregate summary."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (16) did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step 16 data should be a dict, got {type(d)}"
    assert d.get("count") == 14, f"expected count=14, got {d.get('count')}"
    assert gu.close(d["sum"], 52.171, rtol=1e-3), f"sum wrong: {d['sum']}"
    assert gu.close(d["mean"], 3.7265, rtol=1e-3), f"mean wrong: {d['mean']}"
    assert gu.close(d["max"], 10.0), f"max wrong: {d['max']}"
    assert gu.close(d["min"], 0.0), f"min wrong: {d['min']}"


@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code quality report — never a pass/fail gate."""
    print("code_quality:", gu.code_quality_report(SOL))
