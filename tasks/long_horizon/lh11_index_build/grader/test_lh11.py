"""Grader for long_horizon/lh11_index_build.

Drives the candidate's 6-step TF-IDF index CLI chain, verifies the provenance
link at each step, and compares each step's output to the canonical fixture
(precomputed by running the gold chain). The candidate's own step output is fed
forward, so an early error cascades. One test per step plus a cumulative test on
the top-3 ranking; the runner's partial score tracks how far the chain stayed
correct.

The planted defect lives in step 3 (document frequency), so a correct solution
passes all six step tests while a solution that miscomputes df fails steps 3-6.
"""
import json
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "long_horizon", "lh11_index_build"
TASK_DIR = Path(__file__).resolve().parents[1]
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
INPUT = TASK_DIR / "data" / "docs.json"
EXPECTED = json.loads((TASK_DIR / "expected" / "steps.json").read_text())
N_STEPS = 6


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    out = tmp_path_factory.mktemp("lh11")
    return gu.run_provenance_chain(SOL, INPUT, N_STEPS, out, timeout_per_step=15)


def _approx_equal(a, b):
    """Recursive structural comparison: floats by tolerance, everything else exact."""
    if isinstance(b, dict):
        if not isinstance(a, dict) or a.keys() != b.keys():
            return False
        return all(_approx_equal(a[k], v) for k, v in b.items())
    if isinstance(b, list):
        return isinstance(a, list) and len(a) == len(b) and \
            all(_approx_equal(x, y) for x, y in zip(a, b))
    if isinstance(b, bool):
        return a is b
    if isinstance(b, float):
        return isinstance(a, (int, float)) and not isinstance(a, bool) and gu.close(a, b)
    return a == b


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
    exp = EXPECTED["6"]["data"]
    assert d["top"] == exp["top"], f"top-3 ids wrong: {d['top']}"
    assert len(d["scores"]) == len(exp["scores"]) and \
        all(gu.close(s, e) for s, e in zip(d["scores"], exp["scores"])), \
        f"top-3 scores wrong: {d['scores']}"


@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
