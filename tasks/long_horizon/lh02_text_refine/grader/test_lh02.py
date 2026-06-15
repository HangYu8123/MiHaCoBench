"""Grader for long_horizon/lh02_text_refine.

Runs the candidate's 4-step CLI chain, verifies the provenance link at each
step, and compares each step's output to the canonical fixture. The candidate's
own step output is fed forward, so an early error cascades. One test per step
plus a final cumulative test.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh02_text_refine"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 4


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh02")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursively compare two values with tolerance for floats."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            return False
        return all(_approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, (int, float)) and isinstance(a, (int, float)):
        return gu.close(a, b)
    return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], f"step {k} did not run: {chain}"
    assert rec["prov_ok"], f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), \
        f"step {k} data wrong.\n  got:      {rec['data']}\n  expected: {EXPECTED[str(k)]['data']}"


def test_final_cumulative(chain):
    """All 4 steps ran correctly and the final top-k result is right."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (step 4) did not run"
    d = final["data"]
    # top-3: fox=3, the=3, quick=2  (fox before the because 'f' < 't')
    assert isinstance(d, list), "step 4 data must be a list"
    assert len(d) == 3, f"expected 3 top-k entries, got {len(d)}"
    assert d[0] == ["fox", 3], f"first entry wrong: {d[0]}"
    assert d[1] == ["the", 3], f"second entry wrong: {d[1]}"
    assert d[2] == ["quick", 2], f"third entry wrong: {d[2]}"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
