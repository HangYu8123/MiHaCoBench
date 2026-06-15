"""Grader for data_analysis/d03_customer_segments.

Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d03_customer_segments"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
analyze = gu.load_callable(SOL, "solution.py", "analyze")

# Task-level paths
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "customers.csv"
EXPECTED_JSON = TASK_DIR / "expected" / "d03.json"

# Load expected values once
_expected = json.loads(EXPECTED_JSON.read_text())
EXPECTED_BEST_K: int = _expected["best_k"]
EXPECTED_SILHOUETTE: float = _expected["silhouette"]
EXPECTED_INERTIA: dict[str, float] = _expected["inertia_by_k"]
EXPECTED_CLUSTER_SIZES: list[int] = _expected["cluster_sizes"]

# Load the committed dataset once
_df = pd.read_csv(DATA_CSV)


# ---------------------------------------------------------------------------
# Test 1 — best_k is correct integer
# ---------------------------------------------------------------------------
def test_best_k_is_four():
    """best_k must equal 4 (the number of blobs in the dataset)."""
    result = analyze(_df)
    assert result["best_k"] == EXPECTED_BEST_K, (
        f"Expected best_k={EXPECTED_BEST_K}, got {result['best_k']}"
    )


# ---------------------------------------------------------------------------
# Test 2 — silhouette score within tolerance
# ---------------------------------------------------------------------------
def test_silhouette_within_tolerance():
    """Silhouette score for best_k must be within atol=0.02 of expected."""
    result = analyze(_df)
    assert gu.close(result["silhouette"], EXPECTED_SILHOUETTE, rtol=0.0, atol=0.02), (
        f"Silhouette {result['silhouette']:.6f} not close to {EXPECTED_SILHOUETTE:.6f} (atol=0.02)"
    )


# ---------------------------------------------------------------------------
# Test 3 — inertia_by_k has all keys "2".."6" with decreasing inertia
# ---------------------------------------------------------------------------
def test_inertia_by_k_keys_and_trend():
    """inertia_by_k must have string keys '2' through '6' with decreasing values."""
    result = analyze(_df)
    idict = result["inertia_by_k"]
    assert set(idict.keys()) == {"2", "3", "4", "5", "6"}, (
        f"Expected keys {{2..6}}, got {set(idict.keys())}"
    )
    # Inertia must decrease as k increases (more clusters = less inertia)
    inertias = [idict[str(k)] for k in range(2, 7)]
    for i in range(len(inertias) - 1):
        assert inertias[i] > inertias[i + 1], (
            f"Inertia should be decreasing: k={i+2} inertia={inertias[i]} <= k={i+3} inertia={inertias[i+1]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — inertia_by_k values within tolerance of expected
# ---------------------------------------------------------------------------
def test_inertia_by_k_values():
    """Each inertia value must be within rtol=0.01 of expected."""
    result = analyze(_df)
    idict = result["inertia_by_k"]
    for k_str, expected_val in EXPECTED_INERTIA.items():
        actual = idict[str(k_str)]
        assert gu.close(actual, expected_val, rtol=0.01, atol=1.0), (
            f"Inertia for k={k_str}: expected {expected_val:.4f}, got {actual:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 5 — cluster_sizes length, sum, and sorted-descending
# ---------------------------------------------------------------------------
def test_cluster_sizes_structure():
    """cluster_sizes must have length==best_k, sum==400, be sorted descending."""
    result = analyze(_df)
    best_k = result["best_k"]
    sizes = result["cluster_sizes"]
    assert len(sizes) == best_k, (
        f"cluster_sizes length {len(sizes)} != best_k {best_k}"
    )
    assert sum(sizes) == 400, f"cluster_sizes sum {sum(sizes)} != 400"
    assert sizes == sorted(sizes, reverse=True), "cluster_sizes must be sorted descending"


# ---------------------------------------------------------------------------
# Test 6 — cluster_sizes match expected values
# ---------------------------------------------------------------------------
def test_cluster_sizes_values():
    """cluster_sizes must match expected counts (deterministic with random_state=0)."""
    result = analyze(_df)
    assert result["cluster_sizes"] == EXPECTED_CLUSTER_SIZES, (
        f"Expected cluster_sizes {EXPECTED_CLUSTER_SIZES}, got {result['cluster_sizes']}"
    )


# ---------------------------------------------------------------------------
# Test 7 — source uses required sklearn functions
# ---------------------------------------------------------------------------
def test_source_uses_required_functions():
    """Solution source must invoke KMeans, silhouette_score, and StandardScaler."""
    usage = gu.source_uses(SOL, ["KMeans", "silhouette_score", "StandardScaler"])
    for fn_name, present in usage.items():
        assert present, f"Required function/class '{fn_name}' not found in solution source"


# ---------------------------------------------------------------------------
# Test 8 — CLI produces results.json + >=3 valid PNGs
# ---------------------------------------------------------------------------
def test_cli_produces_outputs(tmp_path):
    """main() must write results.json and at least 3 valid PNG files."""
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"

    # Check results.json
    results_file = tmp_path / "results.json"
    assert results_file.exists(), "results.json not found in output dir"
    data = json.loads(results_file.read_text())
    assert "best_k" in data
    assert "silhouette" in data
    assert "inertia_by_k" in data
    assert "cluster_sizes" in data

    # Check >=3 valid PNGs
    n_pngs = gu.count_valid_pngs(tmp_path)
    assert n_pngs >= 3, f"Expected >=3 valid PNGs, found {n_pngs}"


# ---------------------------------------------------------------------------
# Test 9 — CLI results.json best_k is correct
# ---------------------------------------------------------------------------
def test_cli_results_best_k(tmp_path):
    """results.json written by main() must have best_k==4."""
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads((tmp_path / "results.json").read_text())
    assert data["best_k"] == EXPECTED_BEST_K


# ---------------------------------------------------------------------------
# Advisory code quality test
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code quality check — printed but never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
