"""Grader for data_analysis/d07_paired_design.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The DS-1000 twist: the data is a *paired* before/after design, so the correct
test is the PAIRED t-test (scipy.stats.ttest_rel). The grader computes the
paired reference INLINE with scipy (no precomputed expected/ fixture) and also
computes the unpaired statistic so the discrimination is explicit:

  * PASS_TO_PASS  (gold AND broken): n, mean_before, mean_after, mean_diff —
    these do not depend on which test is used.
  * FAIL_TO_PASS  (gold True, broken False): t_stat / p_value match the PAIRED
    reference, and the surface-form constraint (ttest_rel present, ttest_ind
    absent) holds. The broken solution runs the unpaired test, so its t_stat
    matches the unpaired reference instead and it imports ttest_ind.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy.stats

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d07_paired_design"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the committed dataset (from task data dir — never generated in grader)
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "paired.csv"

# Load the analyze callable
analyze = gu.load_callable(SOL, "solution.py", "analyze")

# Load the dataset once and call analyze once
_df = pd.read_csv(DATA_CSV)
_result = analyze(_df)

# --- Inline reference computation (the PAIRED test is the correct one) -------
_before = _df["before"].to_numpy(dtype=float)
_after = _df["after"].to_numpy(dtype=float)
_n = int(len(_df))
_diffs = _after - _before
_mean_before = float(np.mean(_before))
_mean_after = float(np.mean(_after))
_mean_diff = float(np.mean(_diffs))
_std_diff = float(np.std(_diffs, ddof=1))

# Paired reference (correct): scipy.stats.ttest_rel(after, before)
_ref_t_paired, _ref_p_paired = scipy.stats.ttest_rel(_after, _before)
_ref_t_paired = float(_ref_t_paired)
_ref_p_paired = float(_ref_p_paired)

# Unpaired reference (the wrong test the broken solution uses) — used only to
# confirm the two references are well separated so the grader truly discriminates.
_ref_t_unpaired, _ref_p_unpaired = scipy.stats.ttest_ind(_after, _before)
_ref_t_unpaired = float(_ref_t_unpaired)
_ref_p_unpaired = float(_ref_p_unpaired)

# Paired effect size and 95% CI reference
_ref_cohens_d = _mean_diff / _std_diff
_ref_se = _std_diff / math.sqrt(_n)
_ref_tcrit = float(scipy.stats.t.ppf(0.975, df=_n - 1))
_ref_ci_low = _mean_diff - _ref_tcrit * _ref_se
_ref_ci_high = _mean_diff + _ref_tcrit * _ref_se

REQUIRED_KEYS = {
    "n", "mean_before", "mean_after", "mean_diff", "t_stat",
    "p_value", "cohens_d", "ci95_low", "ci95_high", "reject_null",
}


# ---------------------------------------------------------------------------
# Sanity: the dataset must genuinely discriminate paired from unpaired.
# (Not a candidate test — guards the fixture itself.)
# ---------------------------------------------------------------------------
def test_dataset_discriminates_paired_vs_unpaired():
    assert _ref_p_paired < 0.05, (
        f"fixture broken: paired test should be significant, p={_ref_p_paired}"
    )
    assert _ref_p_unpaired > 0.05, (
        f"fixture broken: unpaired test should NOT be significant, p={_ref_p_unpaired}"
    )
    # The two t-statistics must be far apart so a 1e-3 tolerance separates them.
    assert abs(_ref_t_paired - _ref_t_unpaired) > 1.0


# ---------------------------------------------------------------------------
# Test 1: return type and required keys
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    assert isinstance(_result, dict), "analyze() must return a dict"
    missing = REQUIRED_KEYS - set(_result.keys())
    assert not missing, f"Missing keys in result: {missing}"


# ---------------------------------------------------------------------------
# Test 2: n correct (PASS_TO_PASS)
# ---------------------------------------------------------------------------
def test_n():
    assert _result["n"] == _n, f"n mismatch: got {_result['n']}, expected {_n}"


# ---------------------------------------------------------------------------
# Test 3: mean_before / mean_after correct (PASS_TO_PASS — test-independent)
# ---------------------------------------------------------------------------
def test_group_means():
    assert gu.close(_result["mean_before"], _mean_before, rtol=1e-3), (
        f"mean_before mismatch: got {_result['mean_before']}, expected {_mean_before}"
    )
    assert gu.close(_result["mean_after"], _mean_after, rtol=1e-3), (
        f"mean_after mismatch: got {_result['mean_after']}, expected {_mean_after}"
    )


# ---------------------------------------------------------------------------
# Test 4: mean_diff correct (PASS_TO_PASS — test-independent)
# ---------------------------------------------------------------------------
def test_mean_diff():
    md = _result["mean_diff"]
    assert isinstance(md, float), "mean_diff must be a float"
    assert gu.close(md, _mean_diff, rtol=1e-3), (
        f"mean_diff mismatch: got {md}, expected {_mean_diff}"
    )


# ---------------------------------------------------------------------------
# Test 5: reject_null True and p_value below 0.05 (paired test is significant)
# ---------------------------------------------------------------------------
def test_reject_null_and_significance():
    p = _result["p_value"]
    assert isinstance(p, float), "p_value must be a float"
    assert p < 0.05, f"p_value must be < 0.05 (paired null rejected), got {p}"
    assert _result["reject_null"] is True, "reject_null must be True"


# ---------------------------------------------------------------------------
# Test 6: t_stat matches the PAIRED reference (FAIL_TO_PASS)
#   The broken solution runs the unpaired test, whose t differs by >1.
# ---------------------------------------------------------------------------
def test_t_stat_matches_paired_reference():
    t = _result["t_stat"]
    assert isinstance(t, float), "t_stat must be a float"
    assert t > 0, f"t_stat must be positive (after > before), got {t}"
    assert gu.close(t, _ref_t_paired, rtol=1e-3), (
        f"t_stat must match the PAIRED reference {_ref_t_paired} (got {t}); "
        f"the unpaired statistic is {_ref_t_unpaired} — use scipy.stats.ttest_rel."
    )


# ---------------------------------------------------------------------------
# Test 7: p_value matches the PAIRED reference (FAIL_TO_PASS)
# ---------------------------------------------------------------------------
def test_p_value_matches_paired_reference():
    p = _result["p_value"]
    assert gu.close(p, _ref_p_paired, rtol=1e-3, atol=1e-30), (
        f"p_value must match the PAIRED reference {_ref_p_paired} (got {p}); "
        f"the unpaired p-value is {_ref_p_unpaired}."
    )


# ---------------------------------------------------------------------------
# Test 8: cohens_d (paired effect size = mean_diff / std(diffs, ddof=1))
# ---------------------------------------------------------------------------
def test_cohens_d():
    d = _result["cohens_d"]
    assert isinstance(d, float), "cohens_d must be a float"
    assert d > 0, f"cohens_d must be positive, got {d}"
    assert gu.close(d, _ref_cohens_d, rtol=1e-3), (
        f"cohens_d mismatch: got {d}, expected {_ref_cohens_d}"
    )


# ---------------------------------------------------------------------------
# Test 9: 95% CI of the mean paired difference
# ---------------------------------------------------------------------------
def test_confidence_interval():
    ci_low = _result["ci95_low"]
    ci_high = _result["ci95_high"]
    assert ci_low < ci_high, "ci95_low must be less than ci95_high"
    assert ci_low > 0, f"ci95_low should be > 0 (effect is positive), got {ci_low}"
    assert gu.close(ci_low, _ref_ci_low, rtol=1e-3), (
        f"ci95_low mismatch: got {ci_low}, expected {_ref_ci_low}"
    )
    assert gu.close(ci_high, _ref_ci_high, rtol=1e-3), (
        f"ci95_high mismatch: got {ci_high}, expected {_ref_ci_high}"
    )


# ---------------------------------------------------------------------------
# Test 10: surface-form — must use ttest_rel and must NOT use ttest_ind
#   (FAIL_TO_PASS: the broken solution imports the unpaired ttest_ind)
# ---------------------------------------------------------------------------
def test_surface_form_paired_test():
    usage = gu.source_uses(SOL, ["ttest_rel", "ttest_ind"])
    assert usage["ttest_rel"], (
        "solution.py must invoke scipy.stats.ttest_rel (paired test surface-form)"
    )
    assert not usage["ttest_ind"], (
        "solution.py must NOT use scipy.stats.ttest_ind — the design is paired"
    )


# ---------------------------------------------------------------------------
# Test 11: CLI writes results.json with matching t_stat (paired reference)
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
    missing = REQUIRED_KEYS - set(data.keys())
    assert not missing, f"results.json missing keys: {missing}"
    assert gu.close(data["t_stat"], _ref_t_paired, rtol=1e-3), (
        f"results.json t_stat must match PAIRED reference {_ref_t_paired}, "
        f"got {data['t_stat']}"
    )
    assert gu.close(data["mean_diff"], _mean_diff, rtol=1e-3), (
        f"results.json mean_diff mismatch: {data['mean_diff']}"
    )
    assert data["reject_null"] is True, "results.json reject_null must be True"


# ---------------------------------------------------------------------------
# Test 12: CLI writes at least 2 valid PNG files
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
