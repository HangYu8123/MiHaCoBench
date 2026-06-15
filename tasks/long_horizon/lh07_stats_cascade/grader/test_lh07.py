"""Grader for long_horizon/lh07_stats_cascade.

Runs the candidate's CLI step chain, verifies the provenance link at each step,
and compares each step's output to the canonical fixture. The candidate's own
step output is fed forward, so an early error cascades. One test per step plus
a final cumulative test; the runner's partial score tracks chain depth.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh07_stats_cascade"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "input.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 14


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh07")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursive approximate equality for nested dicts/lists/scalars."""
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            return False
        return all(_approx_equal(x, y) for x, y in zip(a, b))
    if a is None or b is None:
        return a == b
    return gu.close(float(a), float(b), rtol=1e-3)


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], f"step {k} did not run: {chain}"
    assert rec["prov_ok"], f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), (
        f"step {k} data mismatch:\n  got:      {rec['data']}\n"
        f"  expected: {EXPECTED[str(k)]['data']}"
    )


def test_final_cumulative(chain):
    """Step 14 must produce the correct aggregate over the top-8 list."""
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step (14) missing or failed"
    d = final["data"]
    assert isinstance(d, dict), "step 14 data must be a dict"
    assert d.get("count") == 8, f"expected count=8, got {d.get('count')}"
    assert gu.close(float(d["sum"]), 60.98316666666666, rtol=1e-3), f"sum wrong: {d['sum']}"
    assert gu.close(float(d["mean"]), 7.622895833333333, rtol=1e-3), f"mean wrong: {d['mean']}"
    assert gu.close(float(d["max"]), 12.1795, rtol=1e-3), f"max wrong: {d['max']}"
    assert gu.close(float(d["min"]), 6.410333333333334, rtol=1e-3), f"min wrong: {d['min']}"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
