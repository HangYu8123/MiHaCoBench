"""Grader for data_analysis/d05_experiment_anova.

Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference
(which omits Bonferroni correction, producing a different significant_pairs).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d05_experiment_anova"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Paths relative to the task directory (grader/ is one level inside the task dir)
_TASK_DIR = Path(__file__).resolve().parents[1]
_DATA_PATH = _TASK_DIR / "data" / "experiment.csv"
_EXPECTED_PATH = _TASK_DIR / "expected" / "d05.json"

# Load expected ground truth once (pre-computed from the gold solution)
with open(_EXPECTED_PATH) as _fh:
    _EXPECTED = json.load(_fh)

# Load the solution under test and the analyze callable
analyze = gu.load_callable(SOL, "solution.py", "analyze")

# Load the committed dataset once
_DF = pd.read_csv(_DATA_PATH)
_RESULT = analyze(_DF)


# ---------------------------------------------------------------------------
# Test 1: required keys present
# ---------------------------------------------------------------------------
def test_result_keys():
    required = {"group_means", "anova_F", "anova_p", "significant", "significant_pairs"}
    assert required.issubset(set(_RESULT.keys())), (
        f"missing keys: {required - set(_RESULT.keys())}"
    )


# ---------------------------------------------------------------------------
# Test 2: group_means within tolerance
# ---------------------------------------------------------------------------
def test_group_means():
    expected_means = _EXPECTED["group_means"]
    actual_means = _RESULT["group_means"]
    for group in ("ctrl", "low", "high"):
        assert group in actual_means, f"group '{group}' missing from group_means"
        assert gu.close(actual_means[group], expected_means[group], rtol=1e-3), (
            f"group_means['{group}']: got {actual_means[group]}, "
            f"expected {expected_means[group]}"
        )


# ---------------------------------------------------------------------------
# Test 3: ANOVA F-statistic and p-value (sign / order-of-magnitude check)
# ---------------------------------------------------------------------------
def test_anova_statistic():
    assert gu.close(_RESULT["anova_F"], _EXPECTED["anova_F"], rtol=1e-3), (
        f"anova_F: got {_RESULT['anova_F']}, expected {_EXPECTED['anova_F']}"
    )
    # p is tiny (~2e-76); we just verify it is below alpha
    assert _RESULT["anova_p"] < 0.05, (
        f"anova_p should be < 0.05 but got {_RESULT['anova_p']}"
    )


# ---------------------------------------------------------------------------
# Test 4: significant flag
# ---------------------------------------------------------------------------
def test_significant_flag():
    assert _RESULT["significant"] is True, (
        f"significant should be True (ANOVA p << 0.05), got {_RESULT['significant']}"
    )


# ---------------------------------------------------------------------------
# Test 5: significant_pairs matches expected (Bonferroni-corrected)
#          ctrl vs low is NOT significant after Bonferroni → must be absent
# ---------------------------------------------------------------------------
def test_significant_pairs():
    actual = _RESULT["significant_pairs"]
    expected = _EXPECTED["significant_pairs"]
    # Normalise to frozensets for order-invariant comparison
    actual_set = {tuple(p) for p in actual}
    expected_set = {tuple(p) for p in expected}
    assert actual_set == expected_set, (
        f"significant_pairs mismatch.\n"
        f"  got:      {sorted(actual)}\n"
        f"  expected: {sorted(expected)}\n"
        "Hint: check that you apply Bonferroni correction (multiply raw p by 3)."
    )


# ---------------------------------------------------------------------------
# Test 6: surface-form constraint — must call f_oneway (not hand-rolled)
# ---------------------------------------------------------------------------
def test_source_uses_f_oneway():
    uses = gu.source_uses(SOL, ["f_oneway"])
    assert uses["f_oneway"], "solution must call scipy.stats.f_oneway"


# ---------------------------------------------------------------------------
# Test 7: surface-form constraint — must call ttest_ind
# ---------------------------------------------------------------------------
def test_source_uses_ttest_ind():
    uses = gu.source_uses(SOL, ["ttest_ind"])
    assert uses["ttest_ind"], "solution must call scipy.stats.ttest_ind"


# ---------------------------------------------------------------------------
# Test 8: CLI writes results.json with correct significant_pairs
# ---------------------------------------------------------------------------
def test_cli_results_json(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(_DATA_PATH), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"CLI exited with {proc.returncode}.\nstderr: {proc.stderr}"
    )
    results_file = tmp_path / "results.json"
    assert results_file.exists(), "results.json was not written"
    with open(results_file) as fh:
        cli_result = json.load(fh)

    assert "significant_pairs" in cli_result
    actual_set = {tuple(p) for p in cli_result["significant_pairs"]}
    expected_set = {tuple(p) for p in _EXPECTED["significant_pairs"]}
    assert actual_set == expected_set, (
        f"CLI results.json significant_pairs mismatch: {cli_result['significant_pairs']}"
    )
    assert cli_result.get("significant") is True


# ---------------------------------------------------------------------------
# Test 9: CLI writes >= 2 valid PNGs (boxplot.png + errorbar.png)
# ---------------------------------------------------------------------------
def test_cli_plots(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(_DATA_PATH), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr

    boxplot = tmp_path / "boxplot.png"
    errorbar = tmp_path / "errorbar.png"
    assert boxplot.exists(), "boxplot.png not written"
    assert errorbar.exists(), "errorbar.png not written"
    assert gu.png_is_valid(boxplot), "boxplot.png is not a valid non-trivial PNG"
    assert gu.png_is_valid(errorbar), "errorbar.png is not a valid non-trivial PNG"
    assert gu.count_valid_pngs(tmp_path) >= 2, "fewer than 2 valid PNGs in output dir"


# ---------------------------------------------------------------------------
# Test 10 (advisory): code quality report — never asserted
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a pass/fail gate
