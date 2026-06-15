"""Grader for long_horizon/lh10_mega_etl.

Runs the candidate's 20-step CLI pipeline, verifies the provenance chain at each
step, and compares each step's output to the canonical fixture in expected/steps.json.
The candidate's own step output is fed forward, so an early error cascades.

One test per step (test_step[1] .. test_step[20]) plus a final cumulative test
(test_final_cumulative) and an advisory code-quality test.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh10_mega_etl"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 20


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh10")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursively compare two values with float tolerance."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            return False
        return all(_approx_equal(x, y) for x, y in zip(a, b))
    if b is None:
        return a is None
    try:
        return gu.close(float(a), float(b), rtol=1e-4)
    except (TypeError, ValueError):
        return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    """Each step must run, produce a valid provenance link, and match the fixture."""
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], (
        f"step {k} did not run — chain so far: {chain}"
    )
    assert rec["prov_ok"], (
        f"step {k} provenance does not match the consumed artifact"
    )
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), (
        f"step {k} data mismatch\n  got:      {rec['data']}\n  expected: {EXPECTED[str(k)]['data']}"
    )


def test_final_cumulative(chain):
    """Step 20 must produce the correct aggregate summary."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (20) did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step 20 data must be a dict, got {type(d)}"
    assert d.get("count") == 5, f"step 20 count must be 5, got {d.get('count')}"
    assert gu.close(d["sum"], EXPECTED["20"]["data"]["sum"], rtol=1e-4), (
        f"step 20 sum mismatch: {d['sum']} vs {EXPECTED['20']['data']['sum']}"
    )
    assert gu.close(d["mean"], EXPECTED["20"]["data"]["mean"], rtol=1e-4), (
        f"step 20 mean mismatch: {d['mean']} vs {EXPECTED['20']['data']['mean']}"
    )
    assert gu.close(d["min"], EXPECTED["20"]["data"]["min"], rtol=1e-4), (
        f"step 20 min mismatch: {d['min']} vs {EXPECTED['20']['data']['min']}"
    )
    assert gu.close(d["max"], EXPECTED["20"]["data"]["max"], rtol=1e-4), (
        f"step 20 max mismatch: {d['max']} vs {EXPECTED['20']['data']['max']}"
    )


@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory: print code-quality metrics (never asserts)."""
    print("code_quality:", gu.code_quality_report(SOL))
