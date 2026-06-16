"""Grader for compositional/cb03_contingency_report.

Tests the public contract only (see TASK.md).

Validity invariant:
  PASSES on the gold reference (all tests).
  FAILS on the broken reference (which runs chi2_contingency on a
  collapsed 2-column table, producing wrong dof and wrong chi2).

Tests (>=6):
  1. test_required_keys       — all 8 keys present
  2. test_table_exact         — contingency table counts exact (int)
  3. test_chi2_close          — chi2 statistic within rtol=1e-3  [BROKEN: fails]
  4. test_dof_exact           — dof is exact int == 2              [BROKEN: fails]
  5. test_reject_null         — reject_null reflects p < 0.05
  6. test_cramers_v           — Cramér's V within rtol=1e-3
  7. test_ci95_bounds         — CI bounds within rtol=0.05
  8. test_source_uses         — chi2_contingency in source
  9. test_missing_column      — KeyError or ValueError for missing column
 10. test_code_quality        — advisory only
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb03_contingency_report"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

_TASK_DIR = Path(__file__).resolve().parents[1]
_DATA_PATH = _TASK_DIR / "data" / "survey.csv"
_EXPECTED_PATH = _TASK_DIR / "expected" / "cb03.json"

with open(_EXPECTED_PATH) as _fh:
    _EXPECTED = json.load(_fh)

analyze = gu.load_callable(SOL, "solution.py", "analyze")

_DF = pd.read_csv(_DATA_PATH)
_RESULT = analyze(_DF)


# ---------------------------------------------------------------------------
# Test 1: required keys present
# ---------------------------------------------------------------------------
def test_required_keys():
    required = {"table", "chi2", "dof", "p_value", "cramers_v",
                "ci95_low", "ci95_high", "reject_null"}
    missing = required - set(_RESULT.keys())
    assert not missing, f"Missing keys: {missing}"


# ---------------------------------------------------------------------------
# Test 2: contingency table exact counts
# ---------------------------------------------------------------------------
def test_table_exact():
    tbl = _RESULT["table"]
    expected_tbl = _EXPECTED["table"]
    assert set(tbl.keys()) == set(expected_tbl.keys()), (
        f"table outer keys mismatch: got {set(tbl.keys())}, "
        f"expected {set(expected_tbl.keys())}"
    )
    for grp in expected_tbl:
        assert grp in tbl, f"group '{grp}' missing from table"
        for resp in expected_tbl[grp]:
            assert resp in tbl[grp], f"response '{resp}' missing from table['{grp}']"
            assert tbl[grp][resp] == expected_tbl[grp][resp], (
                f"table['{grp}']['{resp}']: got {tbl[grp][resp]}, "
                f"expected {expected_tbl[grp][resp]}"
            )


# ---------------------------------------------------------------------------
# Test 3: chi2 statistic within tolerance  (BROKEN: fails — wrong chi2)
# ---------------------------------------------------------------------------
def test_chi2_close():
    assert gu.close(_RESULT["chi2"], _EXPECTED["chi2"], rtol=1e-3), (
        f"chi2: got {_RESULT['chi2']}, expected {_EXPECTED['chi2']}"
    )


# ---------------------------------------------------------------------------
# Test 4: dof exact integer  (BROKEN: fails — dof=1 instead of 2)
# ---------------------------------------------------------------------------
def test_dof_exact():
    assert isinstance(_RESULT["dof"], int), (
        f"dof must be an int, got {type(_RESULT['dof'])}"
    )
    assert _RESULT["dof"] == _EXPECTED["dof"], (
        f"dof: got {_RESULT['dof']}, expected {_EXPECTED['dof']}"
    )


# ---------------------------------------------------------------------------
# Test 5: reject_null reflects p < 0.05 (not exact p comparison)
# ---------------------------------------------------------------------------
def test_reject_null():
    # Dataset has genuine significant association: expect True
    assert _RESULT["reject_null"] is True, (
        f"reject_null should be True (chi2 test is significant at alpha=0.05), "
        f"got {_RESULT['reject_null']}"
    )
    # Consistency: reject_null must agree with p_value < 0.05
    expected_reject = _RESULT["p_value"] < 0.05
    assert _RESULT["reject_null"] == expected_reject, (
        f"reject_null ({_RESULT['reject_null']}) inconsistent with "
        f"p_value ({_RESULT['p_value']})"
    )


# ---------------------------------------------------------------------------
# Test 6: Cramér's V within tolerance
# ---------------------------------------------------------------------------
def test_cramers_v():
    assert gu.close(_RESULT["cramers_v"], _EXPECTED["cramers_v"], rtol=1e-3), (
        f"cramers_v: got {_RESULT['cramers_v']}, expected {_EXPECTED['cramers_v']}"
    )


# ---------------------------------------------------------------------------
# Test 7: CI bounds within generous tolerance
# ---------------------------------------------------------------------------
def test_ci95_bounds():
    assert gu.close(_RESULT["ci95_low"], _EXPECTED["ci95_low"], rtol=0.05), (
        f"ci95_low: got {_RESULT['ci95_low']}, expected {_EXPECTED['ci95_low']}"
    )
    assert gu.close(_RESULT["ci95_high"], _EXPECTED["ci95_high"], rtol=0.05), (
        f"ci95_high: got {_RESULT['ci95_high']}, expected {_EXPECTED['ci95_high']}"
    )


# ---------------------------------------------------------------------------
# Test 8: surface-form — must call chi2_contingency
# ---------------------------------------------------------------------------
def test_source_uses():
    uses = gu.source_uses(SOL, ["chi2_contingency"])
    assert uses["chi2_contingency"], (
        "solution must call scipy.stats.chi2_contingency"
    )


# ---------------------------------------------------------------------------
# Test 9: missing column raises KeyError or ValueError
# ---------------------------------------------------------------------------
def test_missing_column():
    import pandas as pd
    bad_df = pd.DataFrame({"group": ["control", "treatment"], "value": [1, 2]})
    with pytest.raises((KeyError, ValueError)):
        analyze(bad_df)


# ---------------------------------------------------------------------------
# Test 10 (advisory): code quality — never asserted
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
