"""Grader for long_horizon/lh12_budget_forecast.

Runs the candidate's 8-step CLI chain, verifies the provenance link at each step,
and compares each step's output to the canonical fixture (precomputed by running
the GOLD chain). The candidate's own step output is fed forward, so an early error
cascades. One test per step plus a final cumulative test on the forecast; the
runner's partial score tracks how far the chain stayed correct.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh12_budget_forecast"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "transactions.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 8


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh12")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    if isinstance(b, dict):
        if not isinstance(a, dict):
            return False
        return all(_approx_equal(a.get(k), v) for k, v in b.items())
    if isinstance(b, list):
        return isinstance(a, list) and len(a) == len(b) and all(
            _approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, str):
        return a == b
    return gu.close(a, b)


@pytest.mark.parametrize("k", range(1, N_STEPS + 1))
def test_step(chain, k):
    rec = next((r for r in chain if r["step"] == k), None)
    assert rec is not None and rec["ran"], f"step {k} did not run: {chain}"
    assert rec["prov_ok"], f"step {k} provenance does not match the consumed artifact"
    assert _approx_equal(rec["data"], EXPECTED[str(k)]["data"]), \
        f"step {k} data wrong: {rec['data']}"


def test_final_cumulative(chain):
    final = next((r for r in chain if r["step"] == N_STEPS), None)
    assert final is not None and final["ran"], "final step missing"
    d = final["data"]
    assert gu.close(d["final_balance"], 19283.523813)
    assert gu.close(d["slope"], 2108.571429)
    assert d["n_months"] == 6


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
