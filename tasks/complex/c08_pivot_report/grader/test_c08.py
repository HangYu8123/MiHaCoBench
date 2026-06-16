"""Grader for complex/c08_pivot_report. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant omits ``fill_value=0`` in ``pivot``, so missing
``(index, column)`` combinations come back as ``NaN`` and the dtype becomes
float. Present-combination values still match numerically, so the
PASS_TO_PASS tests stay green while the FAIL_TO_PASS tests (missing combo == 0,
no NaN, integer dtype) fail.

Tests (>=10):
 1.  test_build_frame_empty_raises          — empty records -> ValueError (frame)
 2.  test_pivot_present_sum_values          — PASS_TO_PASS: present combos sum correct
 3.  test_pivot_present_count_values        — PASS_TO_PASS: present combos count correct
 4.  test_pivot_axes_sorted                 — index/columns ascending
 5.  test_top_n_no_tie                       — PASS_TO_PASS: clear top entries
 6.  test_totals_marginal_sums              — PASS_TO_PASS: marginal sums correct
 7.  test_pivot_missing_combo_is_zero_sum    — FAIL_TO_PASS: absent combo == 0
 8.  test_pivot_no_nan_and_integer_sum       — FAIL_TO_PASS: no NaN + int dtype (sum)
 9.  test_pivot_no_nan_and_integer_count     — FAIL_TO_PASS: no NaN + int dtype (count)
 10. test_totals_labels_are_total            — FAIL_TO_PASS: margin label exactly "Total"
 11. test_top_n_tie_break_ascending          — FAIL_TO_PASS: tie broken by ascending label
 12. test_report_empty_raises                — empty records -> ValueError (Report ctor)
 13. advisory code_quality test
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.api.types import is_integer_dtype

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c08_pivot_report"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the public facade. The grader cares only about report.py.
_mod = gu.load_module(SOL, "report.py", alias="report")
Report = getattr(_mod, "Report")


# Fixed, deterministic dataset. Region totals: East=9, West=6, North=6 (West/North
# tie at 6). Note: combination (East, C), (North, B), (North, C), (West, A) never
# occur — these are the "missing combinations" the contract must fill with 0.
RECORDS = [
    {"region": "East", "product": "A", "units": 3},
    {"region": "East", "product": "A", "units": 2},
    {"region": "East", "product": "B", "units": 4},
    {"region": "West", "product": "B", "units": 5},
    {"region": "West", "product": "C", "units": 1},
    {"region": "North", "product": "A", "units": 6},
]


def _report() -> object:
    return Report(list(RECORDS))


# ========================================================================== #
# Construction / validation
# ========================================================================== #

def test_build_frame_empty_raises():
    """An empty records list raises ValueError at construction time."""
    with pytest.raises(ValueError):
        Report([])


def test_report_empty_raises():
    """Constructing a Report from [] raises ValueError (propagated)."""
    with pytest.raises(ValueError):
        Report([])


# ========================================================================== #
# PASS_TO_PASS — gold AND broken
# ========================================================================== #

def test_pivot_present_sum_values():
    """Present (index, column) combos hold the correct summed value."""
    p = _report().pivot("region", "product", "units", "sum")
    # East/A = 3 + 2 = 5; East/B = 4; West/B = 5; West/C = 1; North/A = 6
    assert gu.close(float(p.loc["East", "A"]), 5.0)
    assert gu.close(float(p.loc["East", "B"]), 4.0)
    assert gu.close(float(p.loc["West", "B"]), 5.0)
    assert gu.close(float(p.loc["West", "C"]), 1.0)
    assert gu.close(float(p.loc["North", "A"]), 6.0)


def test_pivot_present_count_values():
    """Present (index, column) combos hold the correct row count."""
    p = _report().pivot("region", "product", "units", "count")
    # East/A = 2 rows; East/B = 1; West/B = 1; West/C = 1; North/A = 1
    assert gu.close(float(p.loc["East", "A"]), 2.0)
    assert gu.close(float(p.loc["East", "B"]), 1.0)
    assert gu.close(float(p.loc["West", "B"]), 1.0)
    assert gu.close(float(p.loc["West", "C"]), 1.0)
    assert gu.close(float(p.loc["North", "A"]), 1.0)


def test_pivot_axes_sorted():
    """Index and columns are returned in ascending order."""
    p = _report().pivot("region", "product", "units", "sum")
    assert list(p.index) == ["East", "North", "West"]
    assert list(p.columns) == ["A", "B", "C"]


def test_top_n_no_tie():
    """top_n returns the right top entries when totals are unambiguous.

    Product totals: A = 11, B = 9, C = 1 (no ties).
    """
    res = _report().top_n("product", "units", 3)
    assert [label for label, _ in res] == ["A", "B", "C"]
    assert gu.close(float(res[0][1]), 11.0)
    assert gu.close(float(res[1][1]), 9.0)
    assert gu.close(float(res[2][1]), 1.0)


def test_totals_marginal_sums():
    """Row/column marginal sums (and grand total) are correct."""
    t = _report().totals("region", "product", "units", "sum")
    # Row marginals: East=9, North=6, West=6
    assert gu.close(float(t.loc["East", "Total"]), 9.0)
    assert gu.close(float(t.loc["North", "Total"]), 6.0)
    assert gu.close(float(t.loc["West", "Total"]), 6.0)
    # Column marginals: A=11, B=9, C=1
    assert gu.close(float(t.loc["Total", "A"]), 11.0)
    assert gu.close(float(t.loc["Total", "B"]), 9.0)
    assert gu.close(float(t.loc["Total", "C"]), 1.0)
    # Grand total
    assert gu.close(float(t.loc["Total", "Total"]), 21.0)


# ========================================================================== #
# FAIL_TO_PASS — gold true, broken false
# ========================================================================== #

def test_pivot_missing_combo_is_zero_sum():
    """A (index, column) combination absent from the data has value 0 (sum)."""
    p = _report().pivot("region", "product", "units", "sum")
    # (East, C) never occurs -> must be exactly 0, not NaN.
    assert p.loc["East", "C"] == 0
    # (North, B) and (West, A) likewise.
    assert p.loc["North", "B"] == 0
    assert p.loc["West", "A"] == 0


def test_pivot_no_nan_and_integer_sum():
    """sum pivot has NO NaN anywhere and an integer dtype in every column."""
    p = _report().pivot("region", "product", "units", "sum")
    assert not p.isna().any().any(), "pivot must not contain NaN; fill missing with 0"
    for col in p.columns:
        assert is_integer_dtype(p[col].dtype), (
            f"column {col!r} must be an integer dtype, got {p[col].dtype}"
        )


def test_pivot_no_nan_and_integer_count():
    """count pivot has NO NaN anywhere and an integer dtype in every column."""
    p = _report().pivot("region", "product", "units", "count")
    assert not p.isna().any().any(), "count pivot must not contain NaN; fill missing with 0"
    # The missing combo cell must be exactly the integer 0.
    assert p.loc["East", "C"] == 0
    for col in p.columns:
        assert is_integer_dtype(p[col].dtype), (
            f"column {col!r} must be an integer dtype, got {p[col].dtype}"
        )


def test_totals_labels_are_total():
    """The margin row and column are labelled exactly 'Total' (not 'All')."""
    t = _report().totals("region", "product", "units", "sum")
    assert "Total" in t.index, "expected a row labelled exactly 'Total'"
    assert "Total" in t.columns, "expected a column labelled exactly 'Total'"
    assert "All" not in t.index, "must use the label 'Total', not pandas' default 'All'"
    assert "All" not in t.columns, "must use the label 'Total', not pandas' default 'All'"


def test_top_n_tie_break_ascending():
    """A deliberate tie is broken by ascending index label.

    Region totals: East=9, West=6, North=6. West and North tie at 6, so the
    ordering after East must be North (ascending label) then West.
    """
    res = _report().top_n("region", "units", 3)
    assert [label for label, _ in res] == ["East", "North", "West"]
    assert gu.close(float(res[0][1]), 9.0)
    assert gu.close(float(res[1][1]), 6.0)
    assert gu.close(float(res[2][1]), 6.0)


# ========================================================================== #
# Advisory code quality
# ========================================================================== #

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
