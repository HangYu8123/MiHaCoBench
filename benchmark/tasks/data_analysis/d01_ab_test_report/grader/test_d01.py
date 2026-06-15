"""Grader for data_analysis/d01_ab_test_report.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Orientation note: t_stat is B-minus-A, so a positive value means B > A.
The grader checks sign(t_stat) > 0 (B > A confirmed).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d01_ab_test_report"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the committed dataset (from task data dir — never generated in grader)
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "ab_data.csv"
EXPECTED_FILE = TASK_DIR / "expected" / "d01.json"

# Load expected ground truth
with open(EXPECTED_FILE) as _f:
    EXPECTED = json.load(_f)

# Load the analyze callable
analyze = gu.load_callable(SOL, "solution.py", "analyze")

# Load the dataset once
_df = pd.read_csv(DATA_CSV)
_result = analyze(_df)


# ---------------------------------------------------------------------------
# Test 1: return type and required keys
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    required_keys = {
        "group_means", "n", "t_stat", "p_value", "df",
        "cohens_d", "ci95_low", "ci95_high", "reject_null",
    }
    assert isinstance(_result, dict), "analyze() must return a dict"
    missing = required_keys - set(_result.keys())
    assert not missing, f"Missing keys in result: {missing}"


# ---------------------------------------------------------------------------
# Test 2: group means match expected within rtol=1e-3
# ---------------------------------------------------------------------------
def test_group_means():
    gm = _result["group_means"]
    assert isinstance(gm, dict), "group_means must be a dict"
    assert set(gm.keys()) == {"A", "B"}, "group_means must have keys 'A' and 'B'"
    assert gu.close(gm["A"], EXPECTED["group_means"]["A"], rtol=1e-3), (
        f"group_means['A'] mismatch: got {gm['A']}, expected {EXPECTED['group_means']['A']}"
    )
    assert gu.close(gm["B"], EXPECTED["group_means"]["B"], rtol=1e-3), (
        f"group_means['B'] mismatch: got {gm['B']}, expected {EXPECTED['group_means']['B']}"
    )


# ---------------------------------------------------------------------------
# Test 3: sample sizes
# ---------------------------------------------------------------------------
def test_sample_sizes():
    n = _result["n"]
    assert isinstance(n, dict), "n must be a dict"
    assert n["A"] == EXPECTED["n"]["A"], f"n['A'] mismatch: got {n['A']}, expected {EXPECTED['n']['A']}"
    assert n["B"] == EXPECTED["n"]["B"], f"n['B'] mismatch: got {n['B']}, expected {EXPECTED['n']['B']}"


# ---------------------------------------------------------------------------
# Test 4: t_stat value and sign (B > A so positive)
# ---------------------------------------------------------------------------
def test_t_stat():
    t = _result["t_stat"]
    assert isinstance(t, float), "t_stat must be a float"
    assert t > 0, f"t_stat must be positive (B > A), got {t}"
    assert gu.close(t, EXPECTED["t_stat"], rtol=1e-3), (
        f"t_stat mismatch: got {t}, expected {EXPECTED['t_stat']}"
    )


# ---------------------------------------------------------------------------
# Test 5: p_value — check conclusion (reject at alpha=0.05) and magnitude
# ---------------------------------------------------------------------------
def test_p_value_and_reject_null():
    p = _result["p_value"]
    assert isinstance(p, float), "p_value must be a float"
    assert p < 0.05, f"p_value must be < 0.05 (null should be rejected), got {p}"
    assert _result["reject_null"] is True, "reject_null must be True"
    # Check order of magnitude: p should be very small (< 1e-5 for this dataset)
    assert p < 1e-5, f"p_value unexpectedly large: {p} (expected ~2e-9)"


# ---------------------------------------------------------------------------
# Test 6: Cohen's d value within tolerance
# ---------------------------------------------------------------------------
def test_cohens_d():
    d = _result["cohens_d"]
    assert isinstance(d, float), "cohens_d must be a float"
    assert d > 0, f"cohens_d must be positive (B > A), got {d}"
    assert gu.close(d, EXPECTED["cohens_d"], rtol=1e-3), (
        f"cohens_d mismatch: got {d}, expected {EXPECTED['cohens_d']}"
    )


# ---------------------------------------------------------------------------
# Test 7: 95% CI of mean difference (B - A) within tolerance
# ---------------------------------------------------------------------------
def test_confidence_interval():
    ci_low = _result["ci95_low"]
    ci_high = _result["ci95_high"]
    assert ci_low < ci_high, "ci95_low must be less than ci95_high"
    # Both bounds should be positive (true effect is positive and CI is tight)
    assert ci_low > 0, f"ci95_low should be > 0, got {ci_low}"
    assert gu.close(ci_low, EXPECTED["ci95_low"], rtol=1e-3), (
        f"ci95_low mismatch: got {ci_low}, expected {EXPECTED['ci95_low']}"
    )
    assert gu.close(ci_high, EXPECTED["ci95_high"], rtol=1e-3), (
        f"ci95_high mismatch: got {ci_high}, expected {EXPECTED['ci95_high']}"
    )


# ---------------------------------------------------------------------------
# Test 8: surface-form check — must use scipy.stats.ttest_ind
# ---------------------------------------------------------------------------
def test_source_uses_ttest_ind():
    usage = gu.source_uses(SOL, ["ttest_ind"])
    assert usage["ttest_ind"], (
        "solution.py must invoke scipy.stats.ttest_ind (surface-form constraint)"
    )


# ---------------------------------------------------------------------------
# Test 9: CLI writes results.json with required keys within tolerance
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
        "group_means", "n", "t_stat", "p_value", "df",
        "cohens_d", "ci95_low", "ci95_high", "reject_null",
    }
    missing = required_keys - set(data.keys())
    assert not missing, f"results.json missing keys: {missing}"
    # spot-check a few values
    assert gu.close(data["t_stat"], EXPECTED["t_stat"], rtol=1e-3), (
        f"results.json t_stat mismatch: {data['t_stat']}"
    )
    assert gu.close(data["cohens_d"], EXPECTED["cohens_d"], rtol=1e-3), (
        f"results.json cohens_d mismatch: {data['cohens_d']}"
    )
    assert data["reject_null"] is True, "results.json reject_null must be True"


# ---------------------------------------------------------------------------
# Test 10: CLI writes at least 2 valid PNG files
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
