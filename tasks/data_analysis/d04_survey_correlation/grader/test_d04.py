"""Grader for data_analysis/d04_survey_correlation.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken variant has wrong dof (11 instead of 6), which causes test_dof_correct
to fail, satisfying the grader-integrity invariant.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d04_survey_correlation"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the committed dataset (from task data dir — never generated in grader)
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "survey.csv"
EXPECTED_FILE = TASK_DIR / "expected" / "d04.json"

# Load expected ground truth (precomputed from gold reference)
with open(EXPECTED_FILE) as _f:
    EXPECTED = json.load(_f)

# Load the analyze callable
analyze = gu.load_callable(SOL, "solution.py", "analyze")

# Load the dataset and compute result once
_df = pd.read_csv(DATA_CSV)
_result = analyze(_df)


# ---------------------------------------------------------------------------
# Test 1: return type and required keys
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    required_keys = {
        "chi2", "chi2_p", "dof", "dependent",
        "corr_strongest_pair", "corr_strongest_r",
    }
    assert isinstance(_result, dict), "analyze() must return a dict"
    missing = required_keys - set(_result.keys())
    assert not missing, f"Missing keys in result: {missing}"


# ---------------------------------------------------------------------------
# Test 2: chi2 statistic is positive and matches expected within rtol=1e-3
# ---------------------------------------------------------------------------
def test_chi2_statistic():
    chi2 = _result["chi2"]
    assert isinstance(chi2, float), "chi2 must be a float"
    assert chi2 > 0, f"chi2 must be positive, got {chi2}"
    assert gu.close(chi2, EXPECTED["chi2"], rtol=1e-3), (
        f"chi2 mismatch: got {chi2}, expected {EXPECTED['chi2']}"
    )


# ---------------------------------------------------------------------------
# Test 3: chi2_p is very small and dependent flag is True
# ---------------------------------------------------------------------------
def test_chi2_p_and_dependent():
    chi2_p = _result["chi2_p"]
    assert isinstance(chi2_p, float), "chi2_p must be a float"
    # Conclude dependence at alpha=0.05
    assert chi2_p < 0.05, f"chi2_p must be < 0.05 (strong dependence in data), got {chi2_p}"
    assert _result["dependent"] is True, "dependent must be True"
    # Also check order of magnitude: p is very small for this dataset
    assert chi2_p < 1e-20, f"chi2_p unexpectedly large: {chi2_p} (expected ~2.66e-28)"


# ---------------------------------------------------------------------------
# Test 4: degrees of freedom is correct for a 4×3 contingency table
# (4-1)*(3-1) = 6
# ---------------------------------------------------------------------------
def test_dof_correct():
    dof = _result["dof"]
    assert isinstance(dof, int), f"dof must be an int, got {type(dof).__name__}"
    assert dof == EXPECTED["dof"], f"dof mismatch: got {dof}, expected {EXPECTED['dof']} (=(4-1)*(3-1))"


# ---------------------------------------------------------------------------
# Test 5: corr_strongest_pair is correct and sorted alphabetically
# ---------------------------------------------------------------------------
def test_corr_strongest_pair():
    pair = _result["corr_strongest_pair"]
    assert isinstance(pair, list), "corr_strongest_pair must be a list"
    assert len(pair) == 2, f"corr_strongest_pair must have 2 elements, got {len(pair)}"
    assert pair == EXPECTED["corr_strongest_pair"], (
        f"corr_strongest_pair mismatch: got {pair}, expected {EXPECTED['corr_strongest_pair']}"
    )
    # Verify sorted ascending
    assert pair == sorted(pair), f"corr_strongest_pair must be sorted alphabetically: {pair}"


# ---------------------------------------------------------------------------
# Test 6: corr_strongest_r matches expected within rtol=1e-3
# ---------------------------------------------------------------------------
def test_corr_strongest_r():
    r = _result["corr_strongest_r"]
    assert isinstance(r, float), "corr_strongest_r must be a float"
    assert gu.close(r, EXPECTED["corr_strongest_r"], rtol=1e-3), (
        f"corr_strongest_r mismatch: got {r}, expected {EXPECTED['corr_strongest_r']}"
    )
    # The pair income/usage_hours has a strong positive correlation
    assert r > 0.5, f"corr_strongest_r should be > 0.5 for this dataset, got {r}"


# ---------------------------------------------------------------------------
# Test 7: surface-form check — must use scipy.stats.chi2_contingency
# ---------------------------------------------------------------------------
def test_source_uses_chi2_contingency():
    usage = gu.source_uses(SOL, ["chi2_contingency"])
    assert usage["chi2_contingency"], (
        "solution.py must invoke scipy.stats.chi2_contingency (surface-form constraint)"
    )


# ---------------------------------------------------------------------------
# Test 8: CLI writes results.json with required keys within tolerance
# ---------------------------------------------------------------------------
def test_cli_results_json(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"
    results_path = tmp_path / "results.json"
    assert results_path.exists(), "results.json was not written"
    data = json.loads(results_path.read_text())
    required_keys = {
        "chi2", "chi2_p", "dof", "dependent",
        "corr_strongest_pair", "corr_strongest_r",
    }
    missing = required_keys - set(data.keys())
    assert not missing, f"results.json missing keys: {missing}"
    # Spot-check values
    assert gu.close(data["chi2"], EXPECTED["chi2"], rtol=1e-3), (
        f"results.json chi2 mismatch: {data['chi2']}"
    )
    assert data["dependent"] is True, "results.json dependent must be True"
    assert data["dof"] == EXPECTED["dof"], (
        f"results.json dof mismatch: got {data['dof']}, expected {EXPECTED['dof']}"
    )


# ---------------------------------------------------------------------------
# Test 9: CLI writes at least 2 valid PNG files
# ---------------------------------------------------------------------------
def test_cli_pngs(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"
    n_pngs = gu.count_valid_pngs(tmp_path)
    assert n_pngs >= 2, (
        f"Expected at least 2 valid PNG files, found {n_pngs}. "
        f"Files: {list(tmp_path.glob('*.png'))}"
    )


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
