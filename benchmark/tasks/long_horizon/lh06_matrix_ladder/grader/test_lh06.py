"""Grader for long_horizon/lh06_matrix_ladder.

Runs the candidate's 12-step CLI chain and verifies:
  - provenance hash at each step matches the consumed artifact
  - each step's output matches the canonical fixture (expected/steps.json)
  - the final step's aggregate values are correct

The candidate's own step-K output is fed forward into step K+1, so an error in
an early step cascades through all downstream steps. One test per step plus a
final cumulative aggregate test; the runner's partial score tracks chain depth.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh06_matrix_ladder"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 12


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    """Run the full 12-step chain once per test session; reuse the results."""
    out = tmp_path_factory.mktemp("lh06")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(actual, expected):
    """Recursive approximate comparison for nested dicts and lists of floats."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(_approx_equal(actual.get(k), v) for k, v in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        return all(_approx_equal(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, float) or isinstance(expected, int):
        try:
            return gu.close(float(actual), float(expected), rtol=1e-4)
        except (TypeError, ValueError):
            return False
    return actual == expected


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    """Step k must have run, have a valid provenance hash, and match the fixture."""
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], \
        f"step {k} did not run or crashed: {chain}"
    assert rec["prov_ok"], \
        f"step {k} provenance hash does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), \
        f"step {k} data mismatch.\n  got:      {rec['data']}\n  expected: {EXPECTED[str(k)]['data']}"


def test_final_cumulative(chain):
    """The final step's aggregate dict must have all required keys with correct values."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (12) did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step 12 data must be a dict, got {type(d)}"
    assert d.get("count") == 5, f"count wrong: {d.get('count')}"
    assert gu.close(d["total"], 226.0), f"total wrong: {d.get('total')}"
    assert gu.close(d["mean"], 45.2), f"mean wrong: {d.get('mean')}"
    assert gu.close(d["min"], 24.0), f"min wrong: {d.get('min')}"
    assert gu.close(d["max"], 84.0), f"max wrong: {d.get('max')}"


@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code-quality report — never a pass/fail gate."""
    print("code_quality:", gu.code_quality_report(SOL))
