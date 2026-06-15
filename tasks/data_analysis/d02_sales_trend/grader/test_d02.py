"""Grader for data_analysis/d02_sales_trend. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d02_sales_trend"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
analyze = gu.load_callable(SOL, "solution.py", "analyze")

# Committed dataset — never re-generate in the grader
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "sales.csv"
EXPECTED_JSON = TASK_DIR / "expected" / "d02.json"

# Load once at module level
_df = pd.read_csv(DATA_CSV)
_expected = json.loads(EXPECTED_JSON.read_text())
_result = analyze(_df)


# --------------------------------------------------------------------------- #
# Test 1: all required keys are present
# --------------------------------------------------------------------------- #
def test_keys_present():
    required = {
        "slope", "intercept", "r_squared", "trend_direction",
        "anova_F", "anova_p", "seasonal_significant",
        "pearson_price_units", "pearson_p",
    }
    assert required.issubset(set(_result.keys())), (
        f"missing keys: {required - set(_result.keys())}"
    )


# --------------------------------------------------------------------------- #
# Test 2: linear regression numerics within tolerance
# --------------------------------------------------------------------------- #
def test_linear_regression_numerics():
    assert gu.close(_result["slope"], _expected["slope"], rtol=1e-3), (
        f"slope {_result['slope']} != expected {_expected['slope']}"
    )
    assert gu.close(_result["intercept"], _expected["intercept"], rtol=1e-3), (
        f"intercept {_result['intercept']} != expected {_expected['intercept']}"
    )
    assert gu.close(_result["r_squared"], _expected["r_squared"], rtol=1e-3), (
        f"r_squared {_result['r_squared']} != expected {_expected['r_squared']}"
    )


# --------------------------------------------------------------------------- #
# Test 3: trend direction and slope sign
# --------------------------------------------------------------------------- #
def test_trend_direction_up():
    """The dataset has a clear upward trend; slope must be positive."""
    assert _result["trend_direction"] == "up", (
        f"expected trend_direction='up', got {_result['trend_direction']!r}"
    )
    assert float(_result["slope"]) > 0, (
        f"slope must be positive, got {_result['slope']}"
    )


# --------------------------------------------------------------------------- #
# Test 4: ANOVA numerics and seasonal significance
# --------------------------------------------------------------------------- #
def test_anova_numerics():
    assert gu.close(_result["anova_F"], _expected["anova_F"], rtol=1e-3), (
        f"anova_F {_result['anova_F']} != expected {_expected['anova_F']}"
    )


def test_seasonal_significant_true():
    """Strong seasonal pattern means ANOVA should reject null (p < 0.05)."""
    assert _result["seasonal_significant"] is True, (
        f"expected seasonal_significant=True, got {_result['seasonal_significant']}"
    )
    assert float(_result["anova_p"]) < 0.05, (
        f"anova_p should be < 0.05, got {_result['anova_p']}"
    )


# --------------------------------------------------------------------------- #
# Test 5: Pearson correlation — sign and numeric value
# --------------------------------------------------------------------------- #
def test_pearson_negative_correlation():
    """Price is negatively correlated with units by construction."""
    assert float(_result["pearson_price_units"]) < 0, (
        f"expected pearson_price_units < 0, got {_result['pearson_price_units']}"
    )


def test_pearson_numerics():
    assert gu.close(_result["pearson_price_units"], _expected["pearson_price_units"], rtol=1e-3), (
        f"pearson_price_units {_result['pearson_price_units']} != expected "
        f"{_expected['pearson_price_units']}"
    )
    # p-value conclusion: both should be essentially zero (highly significant)
    assert float(_result["pearson_p"]) < 0.05, (
        f"pearson_p should be < 0.05, got {_result['pearson_p']}"
    )


# --------------------------------------------------------------------------- #
# Test 6: surface-form — solution must use the intended scipy functions
# --------------------------------------------------------------------------- #
def test_source_uses_required_functions():
    usage = gu.source_uses(SOL, ["f_oneway", "pearsonr"])
    assert usage["f_oneway"], "solution.py must call scipy.stats.f_oneway"
    assert usage["pearsonr"], "solution.py must call scipy.stats.pearsonr"


# --------------------------------------------------------------------------- #
# Test 7: CLI — results.json written with correct keys
# --------------------------------------------------------------------------- #
def test_cli_results_json(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI failed:\n{proc.stderr}"
    results_file = tmp_path / "results.json"
    assert results_file.exists(), "results.json not written"
    data = json.loads(results_file.read_text())
    required = {
        "slope", "intercept", "r_squared", "trend_direction",
        "anova_F", "anova_p", "seasonal_significant",
        "pearson_price_units", "pearson_p",
    }
    assert required.issubset(set(data.keys())), (
        f"results.json missing keys: {required - set(data.keys())}"
    )
    # Spot-check one numeric key
    assert gu.close(data["slope"], _expected["slope"], rtol=1e-3)


# --------------------------------------------------------------------------- #
# Test 8: CLI — at least 3 valid PNG files produced
# --------------------------------------------------------------------------- #
def test_cli_png_count(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI failed:\n{proc.stderr}"
    count = gu.count_valid_pngs(tmp_path)
    assert count >= 3, f"expected >=3 valid PNGs, found {count}"


# --------------------------------------------------------------------------- #
# Advisory code-quality (never asserted as pass/fail)
# --------------------------------------------------------------------------- #
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
