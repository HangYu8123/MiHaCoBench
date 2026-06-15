"""Grader for long_horizon/lh09_series_build.

Runs the candidate's 18-step CLI chain, verifies the provenance link at each
step, and compares each step's output to the canonical fixture in
expected/steps.json. The candidate's own step output is fed forward so an
early error cascades. One test per step plus a final cumulative test.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh09_series_build"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 18


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh09")
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
    if isinstance(b, (int, float)):
        try:
            return gu.close(float(a), float(b), rtol=1e-4)
        except (TypeError, ValueError):
            return False
    return a == b


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], f"step {k} did not run: {chain}"
    assert rec["prov_ok"], f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), (
        f"step {k} data mismatch.\n  got:      {rec['data']}\n"
        f"  expected: {EXPECTED[str(k)]['data']}"
    )


def test_final_cumulative(chain):
    """Check the final aggregate is fully correct end-to-end."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (18) did not run"
    d = final["data"]
    exp = EXPECTED[str(N_STEPS)]["data"]
    assert isinstance(d, dict), f"step 18 data must be a dict, got {type(d)}"
    assert d.get("count") == exp["count"], (
        f"step 18 count wrong: got {d.get('count')}, expected {exp['count']}"
    )
    assert gu.close(d.get("sum", float("nan")), exp["sum"], rtol=1e-4), (
        f"step 18 sum wrong: got {d.get('sum')}, expected {exp['sum']}"
    )
    assert gu.close(d.get("mean", float("nan")), exp["mean"], rtol=1e-4), (
        f"step 18 mean wrong: got {d.get('mean')}, expected {exp['mean']}"
    )
    assert gu.close(d.get("min", float("nan")), exp["min"], rtol=1e-4), (
        f"step 18 min wrong: got {d.get('min')}, expected {exp['min']}"
    )
    assert gu.close(d.get("max", float("nan")), exp["max"], rtol=1e-4), (
        f"step 18 max wrong: got {d.get('max')}, expected {exp['max']}"
    )


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
