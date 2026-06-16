"""Grader for data_analysis/d06_timeseries_breakpoints.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS >=1 test on the broken reference.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d06_timeseries_breakpoints"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Committed dataset — never re-generate in the grader
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "series.csv"
EXPECTED_JSON = TASK_DIR / "expected" / "d06.json"

# Load once at module level
_df = pd.read_csv(DATA_CSV)
_expected = json.loads(EXPECTED_JSON.read_text())
analyze = gu.load_callable(SOL, "solution.py", "analyze")
_result = analyze(_df)


# --------------------------------------------------------------------------- #
# Test 1: all required keys present
# --------------------------------------------------------------------------- #
def test_keys_present():
    required = {
        "rolling_mean_last", "breakpoint_index",
        "mean_before", "mean_after",
        "t_stat", "p_value", "reject_null",
    }
    missing = required - set(_result.keys())
    assert not missing, f"missing keys: {missing}"


# --------------------------------------------------------------------------- #
# Test 2: breakpoint_index is the exact expected value
# --------------------------------------------------------------------------- #
def test_breakpoint_index_exact():
    assert _result["breakpoint_index"] == _expected["breakpoint_index"], (
        f"breakpoint_index {_result['breakpoint_index']} != expected "
        f"{_expected['breakpoint_index']}"
    )


# --------------------------------------------------------------------------- #
# Test 3: mean_before and mean_after within tolerance
# --------------------------------------------------------------------------- #
def test_means_within_tolerance():
    assert gu.close(_result["mean_before"], _expected["mean_before"], rtol=1e-3), (
        f"mean_before {_result['mean_before']} != expected {_expected['mean_before']}"
    )
    assert gu.close(_result["mean_after"], _expected["mean_after"], rtol=1e-3), (
        f"mean_after {_result['mean_after']} != expected {_expected['mean_after']}"
    )


# --------------------------------------------------------------------------- #
# Test 4: rolling_mean_last within tolerance
# --------------------------------------------------------------------------- #
def test_rolling_mean_last():
    assert gu.close(_result["rolling_mean_last"], _expected["rolling_mean_last"], rtol=1e-3), (
        f"rolling_mean_last {_result['rolling_mean_last']} != expected "
        f"{_expected['rolling_mean_last']}"
    )


# --------------------------------------------------------------------------- #
# Test 5: reject_null must be True (the built-in shift is real)
# --------------------------------------------------------------------------- #
def test_reject_null_is_true():
    assert _result["reject_null"] is True, (
        f"reject_null must be True (strong level shift), got {_result['reject_null']}"
    )
    assert float(_result["p_value"]) < 0.05, (
        f"p_value should be < 0.05, got {_result['p_value']}"
    )


# --------------------------------------------------------------------------- #
# Test 6: surface-form — must use rolling and ttest_ind
# --------------------------------------------------------------------------- #
def test_source_uses_required_functions():
    usage = gu.source_uses(SOL, ["rolling", "ttest_ind"])
    assert usage["rolling"], "solution.py must use pandas rolling (surface-form check)"
    assert usage["ttest_ind"], "solution.py must call scipy.stats.ttest_ind (surface-form check)"


# --------------------------------------------------------------------------- #
# Test 7: CLI — results.json written with correct keys and values
# --------------------------------------------------------------------------- #
def test_cli_results_json(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI failed:\n{proc.stderr}"
    results_file = tmp_path / "results.json"
    assert results_file.exists(), "results.json not written by CLI"
    data = json.loads(results_file.read_text())
    required = {
        "rolling_mean_last", "breakpoint_index",
        "mean_before", "mean_after",
        "t_stat", "p_value", "reject_null",
    }
    missing = required - set(data.keys())
    assert not missing, f"results.json missing keys: {missing}"
    # Spot-check key values
    assert data["breakpoint_index"] == _expected["breakpoint_index"], (
        f"results.json breakpoint_index mismatch: {data['breakpoint_index']}"
    )
    assert gu.close(data["rolling_mean_last"], _expected["rolling_mean_last"], rtol=1e-3), (
        f"results.json rolling_mean_last mismatch: {data['rolling_mean_last']}"
    )


# --------------------------------------------------------------------------- #
# Test 8: CLI — series.png is a valid PNG
# --------------------------------------------------------------------------- #
def test_cli_series_png(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI failed:\n{proc.stderr}"
    png_path = tmp_path / "series.png"
    assert png_path.exists(), "series.png not written by CLI"
    assert gu.png_is_valid(png_path), "series.png is not a valid non-trivial PNG"


# --------------------------------------------------------------------------- #
# Test 9: empty DataFrame raises ValueError
# --------------------------------------------------------------------------- #
def test_empty_df_raises_value_error():
    empty_df = pd.DataFrame(columns=["day", "value"])
    with pytest.raises(ValueError):
        analyze(empty_df)


# --------------------------------------------------------------------------- #
# Advisory code-quality (never asserted as pass/fail)
# --------------------------------------------------------------------------- #
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
