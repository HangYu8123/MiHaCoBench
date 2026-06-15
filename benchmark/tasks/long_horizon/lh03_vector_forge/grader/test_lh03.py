"""Grader for long_horizon/lh03_vector_forge.

Runs the candidate's CLI step chain across all 6 steps, verifies the provenance
link at each step, and compares each step's output to the canonical fixture stored
in expected/steps.json.  The candidate's own step output is fed forward, so an
early error cascades into later steps.  One test per step plus a final cumulative
test; the runner's partial score tracks chain depth.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh03_vector_forge"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 6


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh03")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursively compare nested dicts/lists/floats with tolerance."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list):
            return False
        return len(a) == len(b) and all(_approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, (int, float)):
        try:
            return gu.close(a, b)
        except (TypeError, ValueError):
            return False
    return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    """Each step must run, pass the provenance check, and produce correct data."""
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], f"step {k} did not run: {chain}"
    assert rec["prov_ok"], f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), (
        f"step {k} data wrong.\n  got:      {rec['data']}\n  expected: {EXPECTED[str(k)]['data']}"
    )


def test_final_cumulative(chain):
    """Final aggregate step must produce the correct summary statistics."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (6) missing or did not run"
    d = final["data"]
    assert isinstance(d, dict), f"step 6 data must be a dict, got {type(d)}"
    assert gu.close(d["sum"], 95.0), f"step 6 sum wrong: {d.get('sum')}"
    assert gu.close(d["mean"], 19.0), f"step 6 mean wrong: {d.get('mean')}"
    assert gu.close(d["min"], 15.0), f"step 6 min wrong: {d.get('min')}"
    assert gu.close(d["max"], 23.0), f"step 6 max wrong: {d.get('max')}"
    assert d["count"] == 5, f"step 6 count wrong: {d.get('count')}"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
