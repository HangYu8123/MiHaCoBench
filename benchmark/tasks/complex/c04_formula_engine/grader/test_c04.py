"""Grader for complex/c04_formula_engine.

Tests the public Sheet contract (set_cell / get_value / recalculate) only.
Gold must PASS all tests; broken must FAIL >= 1 test.
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c04_formula_engine"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the Sheet class from the candidate solution.
Sheet = gu.load_callable(SOL, "sheet.py", "Sheet")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_sheet(**cells: str):
    """Create a Sheet with the given cells pre-loaded (keyword → ref=content)."""
    s = Sheet()
    for ref, content in cells.items():
        s.set_cell(ref, content)
    return s


# ---------------------------------------------------------------------------
# 1. Basic arithmetic and cell references
# ---------------------------------------------------------------------------

def test_plain_numbers():
    """Numeric cells are returned as float."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3.5")
    assert gu.close(s.get_value("A1"), 2.0)
    assert gu.close(s.get_value("A2"), 3.5)


def test_text_cell():
    """Text cells are returned as str."""
    s = Sheet()
    s.set_cell("B1", "hello")
    assert s.get_value("B1") == "hello"


def test_formula_addition():
    """=A1+A2 sums two cells."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3")
    s.set_cell("A3", "=A1+A2")
    assert gu.close(s.get_value("A3"), 5.0)


def test_operator_precedence_mul_before_add():
    """* binds tighter than +: =2+3*4 must be 14, not 20."""
    s = Sheet()
    s.set_cell("C1", "=2+3*4")
    result = s.get_value("C1")
    assert gu.close(result, 14.0), f"Expected 14.0, got {result}"


def test_parentheses_override_precedence():
    """Parentheses override default precedence: =(2+3)*4 = 20."""
    s = Sheet()
    s.set_cell("C2", "=(2+3)*4")
    result = s.get_value("C2")
    assert gu.close(result, 20.0), f"Expected 20.0, got {result}"


def test_cell_ref_in_expression():
    """Mixed cell+literal: =A1*A2+1 with A1=2, A2=3 → 7."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3")
    s.set_cell("D1", "=A1*A2+1")
    assert gu.close(s.get_value("D1"), 7.0)


def test_cell_ref_with_parens():
    """=A1*(A2+1) with A1=2, A2=3 → 8."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3")
    s.set_cell("D2", "=A1*(A2+1)")
    assert gu.close(s.get_value("D2"), 8.0)


# ---------------------------------------------------------------------------
# 2. Range aggregation functions
# ---------------------------------------------------------------------------

def test_sum_range():
    """SUM over a column range."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3")
    s.set_cell("A3", "5")
    s.set_cell("B1", "=SUM(A1:A3)")
    assert gu.close(s.get_value("B1"), 10.0)


def test_sum_including_formula_cell():
    """SUM works when part of the range is itself a formula."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3")
    s.set_cell("A3", "=A1+A2")   # 5
    s.set_cell("B1", "=SUM(A1:A3)")
    assert gu.close(s.get_value("B1"), 10.0)


def test_avg_range():
    """AVG over a range."""
    s = Sheet()
    s.set_cell("A1", "10")
    s.set_cell("A2", "20")
    s.set_cell("A3", "30")
    s.set_cell("B2", "=AVG(A1:A3)")
    assert gu.close(s.get_value("B2"), 20.0)


def test_min_max_range():
    """MIN and MAX over a range."""
    s = Sheet()
    s.set_cell("A1", "5")
    s.set_cell("A2", "1")
    s.set_cell("A3", "3")
    s.set_cell("B3", "=MIN(A1:A3)")
    s.set_cell("B4", "=MAX(A1:A3)")
    assert gu.close(s.get_value("B3"), 1.0)
    assert gu.close(s.get_value("B4"), 5.0)


# ---------------------------------------------------------------------------
# 3. IF conditional
# ---------------------------------------------------------------------------

def test_if_true_branch():
    """=IF(A1>A2, 10, 20) with A1=5, A2=3 → 10."""
    s = Sheet()
    s.set_cell("A1", "5")
    s.set_cell("A2", "3")
    s.set_cell("C1", "=IF(A1>A2,10,20)")
    assert gu.close(s.get_value("C1"), 10.0)


def test_if_false_branch():
    """=IF(A1>A2, 10, 20) with A1=1, A2=3 → 20."""
    s = Sheet()
    s.set_cell("A1", "1")
    s.set_cell("A2", "3")
    s.set_cell("C1", "=IF(A1>A2,10,20)")
    assert gu.close(s.get_value("C1"), 20.0)


def test_if_equality_comparison():
    """=IF(A1=A2, 1, 0) with A1=A2=7 → 1."""
    s = Sheet()
    s.set_cell("A1", "7")
    s.set_cell("A2", "7")
    s.set_cell("C2", "=IF(A1=A2,1,0)")
    assert gu.close(s.get_value("C2"), 1.0)


# ---------------------------------------------------------------------------
# 4. Update propagation
# ---------------------------------------------------------------------------

def test_update_propagation():
    """Changing a dependency and calling recalculate propagates correctly."""
    s = Sheet()
    s.set_cell("A1", "2")
    s.set_cell("A2", "3")
    s.set_cell("A3", "=A1+A2")
    assert gu.close(s.get_value("A3"), 5.0)

    s.set_cell("A1", "10")   # update dependency
    s.recalculate()
    assert gu.close(s.get_value("A3"), 13.0)


def test_get_value_lazy_reflects_updates():
    """get_value always reflects the latest cell values without explicit recalculate."""
    s = Sheet()
    s.set_cell("A1", "4")
    s.set_cell("B1", "=A1*2")
    assert gu.close(s.get_value("B1"), 8.0)
    s.set_cell("A1", "7")
    assert gu.close(s.get_value("B1"), 14.0)


# ---------------------------------------------------------------------------
# 5. Cycle detection
# ---------------------------------------------------------------------------

def test_direct_cycle_raises():
    """A1 = =A2 and A2 = =A1 must raise ValueError."""
    s = Sheet()
    s.set_cell("A1", "1")
    s.set_cell("A2", "=A1")
    with pytest.raises(ValueError):
        s.set_cell("A1", "=A2")


def test_self_reference_raises():
    """A cell that directly references itself must raise ValueError."""
    s = Sheet()
    with pytest.raises(ValueError):
        s.set_cell("A1", "=A1")


# ---------------------------------------------------------------------------
# 6. Unset cells treated as 0
# ---------------------------------------------------------------------------

def test_unset_cell_is_zero():
    """Referencing an unset cell returns 0.0."""
    s = Sheet()
    assert gu.close(s.get_value("Z99"), 0.0)


def test_formula_with_unset_ref():
    """Formula referencing an unset cell treats it as 0."""
    s = Sheet()
    s.set_cell("A1", "5")
    s.set_cell("A2", "=A1+B1")   # B1 not set → 0
    assert gu.close(s.get_value("A2"), 5.0)


# ---------------------------------------------------------------------------
# 7. Power operator
# ---------------------------------------------------------------------------

def test_power_operator():
    """=2^3 must equal 8."""
    s = Sheet()
    s.set_cell("A1", "=2^3")
    assert gu.close(s.get_value("A1"), 8.0)


# ---------------------------------------------------------------------------
# Advisory code quality
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
