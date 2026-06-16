"""Grader for compositional/cb04_linalg_solver.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference returns eigenvalues without sorting by magnitude, so
test_eigenvalue_magnitudes_order and test_eigenvalue_magnitudes_values will fail,
while solution/determinant/condition_number/well_conditioned tests pass.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb04_linalg_solver"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Paths committed with the task
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "system.csv"
BAD_CSV = TASK_DIR / "data" / "bad_system.csv"
EXPECTED_FILE = TASK_DIR / "expected" / "cb04.json"

# Load expected ground truth (precomputed by running the gold)
with open(EXPECTED_FILE) as _f:
    EXPECTED = json.load(_f)

# Load the callable
analyze_system = gu.load_callable(SOL, "solution.py", "analyze_system")

# Run once on the committed dataset and cache result
_df = pd.read_csv(DATA_CSV)
_result = analyze_system(_df)


# ---------------------------------------------------------------------------
# Test 1: return type and required keys
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    required_keys = {
        "solution", "condition_number", "eigenvalue_magnitudes",
        "determinant", "well_conditioned",
    }
    assert isinstance(_result, dict), "analyze_system() must return a dict"
    missing = required_keys - set(_result.keys())
    assert not missing, f"Missing keys in result: {missing}"
    extra = set(_result.keys()) - required_keys
    assert not extra, f"Unexpected extra keys: {extra}"


# ---------------------------------------------------------------------------
# Test 2: solution vector — check A @ x ≈ b
# ---------------------------------------------------------------------------
def test_solution_satisfies_system():
    A = _df.iloc[:, :-1].to_numpy(dtype=float)
    b = _df.iloc[:, -1].to_numpy(dtype=float)
    x = np.array(_result["solution"], dtype=float)
    residual = np.max(np.abs(A @ x - b))
    assert residual < 1e-8, f"Solution x does not satisfy A@x=b; max residual={residual:.2e}"


# ---------------------------------------------------------------------------
# Test 3: solution values within tolerance
# ---------------------------------------------------------------------------
def test_solution_values():
    x = _result["solution"]
    expected_x = EXPECTED["solution"]
    assert len(x) == len(expected_x), (
        f"solution length mismatch: got {len(x)}, expected {len(expected_x)}"
    )
    for i, (got, exp) in enumerate(zip(x, expected_x)):
        assert gu.close(got, exp, rtol=1e-4), (
            f"solution[{i}] mismatch: got {got}, expected {exp}"
        )


# ---------------------------------------------------------------------------
# Test 4: condition number within tolerance
# ---------------------------------------------------------------------------
def test_condition_number():
    cond = _result["condition_number"]
    assert isinstance(cond, float), "condition_number must be a float"
    assert gu.close(cond, EXPECTED["condition_number"], rtol=1e-3), (
        f"condition_number mismatch: got {cond}, expected {EXPECTED['condition_number']}"
    )


# ---------------------------------------------------------------------------
# Test 5: eigenvalue_magnitudes are sorted in descending order
# ---------------------------------------------------------------------------
def test_eigenvalue_magnitudes_order():
    mags = _result["eigenvalue_magnitudes"]
    assert isinstance(mags, list), "eigenvalue_magnitudes must be a list"
    assert len(mags) == len(EXPECTED["eigenvalue_magnitudes"]), (
        f"eigenvalue_magnitudes length mismatch: got {len(mags)}, "
        f"expected {len(EXPECTED['eigenvalue_magnitudes'])}"
    )
    for i in range(len(mags) - 1):
        assert mags[i] >= mags[i + 1] - 1e-10, (
            f"eigenvalue_magnitudes not sorted descending at index {i}: "
            f"{mags[i]} < {mags[i+1]}"
        )


# ---------------------------------------------------------------------------
# Test 6: eigenvalue_magnitudes values within tolerance
# ---------------------------------------------------------------------------
def test_eigenvalue_magnitudes_values():
    mags = _result["eigenvalue_magnitudes"]
    expected_mags = EXPECTED["eigenvalue_magnitudes"]
    for i, (got, exp) in enumerate(zip(mags, expected_mags)):
        assert gu.close(got, exp, rtol=1e-4), (
            f"eigenvalue_magnitudes[{i}] mismatch: got {got}, expected {exp}"
        )


# ---------------------------------------------------------------------------
# Test 7: determinant within tolerance
# ---------------------------------------------------------------------------
def test_determinant():
    det = _result["determinant"]
    assert isinstance(det, float), "determinant must be a float"
    assert gu.close(det, EXPECTED["determinant"], rtol=1e-4), (
        f"determinant mismatch: got {det}, expected {EXPECTED['determinant']}"
    )


# ---------------------------------------------------------------------------
# Test 8: well_conditioned boolean flag
# ---------------------------------------------------------------------------
def test_well_conditioned():
    wc = _result["well_conditioned"]
    assert isinstance(wc, bool), f"well_conditioned must be a Python bool, got {type(wc)}"
    assert wc == EXPECTED["well_conditioned"], (
        f"well_conditioned mismatch: got {wc}, expected {EXPECTED['well_conditioned']}"
    )


# ---------------------------------------------------------------------------
# Test 9: non-square input raises ValueError
# ---------------------------------------------------------------------------
def test_non_square_raises_value_error():
    bad_df = pd.read_csv(BAD_CSV)
    with pytest.raises(ValueError):
        analyze_system(bad_df)


# ---------------------------------------------------------------------------
# Test 10: surface-form constraint — must use numpy.linalg
# ---------------------------------------------------------------------------
def test_source_uses_numpy_linalg():
    usage = gu.source_uses(SOL, ["numpy.linalg"])
    assert usage["numpy.linalg"], (
        "solution.py must reference numpy.linalg (surface-form constraint)"
    )


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
