"""Grader for complex/c06_spreadsheet_engine.

Tests the public contract only (see TASK.md).

Validity invariant:
  PASSES on the gold reference (all tests).
  FAILS on the broken reference (propagation tests: the broken variant
  caches the first-evaluated formula value and recalc() is a no-op, so
  after updating an upstream cell the downstream formula still returns
  the old stale value).

Tests (>=10, ClassEval-style — dependency order for partial credit):
  1.  test_load_two_modules            — grader loads >=2 modules (sheet + dag)
  2.  test_networkx_surface_form       — source uses networkx
  3.  test_set_get_literal             — set_value / get_value for literal cells
  4.  test_unset_cell_returns_zero     — unset cell returns 0.0
  5.  test_single_formula              — one formula referencing two literals
  6.  test_formula_with_literal_ref    — formula with numeric literal + cell ref
  7.  test_chained_formula             — A->B->C dependency chain value
  8.  test_recalc_propagates_to_direct — update upstream, recalc, direct dep updates
  9.  test_recalc_propagates_chained   — update upstream, recalc, chained dep updates
  10. test_topological_order_valid     — cells_in_topological_order satisfies deps
  11. test_detect_cycle_false          — detect_cycle returns False on acyclic graph
  12. test_detect_cycle_true           — detect_cycle returns True on cyclic graph
  13. test_cycle_raises_on_get_value   — get_value raises ValueError on cycle
  14. test_cycle_raises_on_recalc      — recalc raises ValueError on cycle
  15. test_operator_precedence         — * binds tighter than + (=2+3*4 == 14.0)
  16. test_parentheses_override_prec   — =(2+3)*4 == 20.0
  17. test_division                    — =A1/B1 correct float division
  18. advisory test_code_quality       — prints gu.code_quality_report (never fails)
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c06_spreadsheet_engine"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the two required modules (sheet + dag) to verify multi-module structure
_sheet_mod = gu.load_module(SOL, "sheet.py", alias="sheet_c06")
_dag_mod = gu.load_module(SOL, "dag.py", alias="dag_c06")

Sheet = getattr(_sheet_mod, "Sheet")


# ========================================================================== #
# Module loading tests
# ========================================================================== #

def test_load_two_modules():
    """Grader must be able to load at least two distinct modules."""
    # Both modules were loaded at import time; just assert they are non-None.
    assert _sheet_mod is not None
    assert _dag_mod is not None


def test_networkx_surface_form():
    """Solution must use networkx (checked via source_uses)."""
    result = gu.source_uses(SOL, ["networkx"])
    assert result["networkx"], (
        "dag.py (or another source file) must import and use networkx"
    )


# ========================================================================== #
# Literal set/get tests
# ========================================================================== #

def test_set_get_literal():
    """set_value stores a float; get_value returns it."""
    s = Sheet()
    s.set_value("A1", 42.0)
    assert gu.close(s.get_value("A1"), 42.0)


def test_unset_cell_returns_zero():
    """A cell that was never set returns 0.0."""
    s = Sheet()
    assert gu.close(s.get_value("Z99"), 0.0)


# ========================================================================== #
# Single formula tests
# ========================================================================== #

def test_single_formula():
    """=A1+B1 evaluates to the sum of the two literal cells."""
    s = Sheet()
    s.set_value("A1", 3.0)
    s.set_value("B1", 7.0)
    s.set_formula("C1", "=A1+B1")
    assert gu.close(s.get_value("C1"), 10.0)


def test_formula_with_literal_ref():
    """Formula mixing a cell reference and a numeric literal."""
    s = Sheet()
    s.set_value("A1", 5.0)
    s.set_formula("B1", "=A1*2")
    assert gu.close(s.get_value("B1"), 10.0)


# ========================================================================== #
# Chained formula test
# ========================================================================== #

def test_chained_formula():
    """A->B->C dependency chain computes the correct value on get_value."""
    s = Sheet()
    s.set_value("A1", 4.0)
    s.set_formula("B1", "=A1+1")    # B1 = 5.0
    s.set_formula("C1", "=B1*3")    # C1 = 15.0
    assert gu.close(s.get_value("C1"), 15.0)


# ========================================================================== #
# Propagation tests (these FAIL on the broken variant)
# ========================================================================== #

def test_recalc_propagates_to_direct():
    """After updating an upstream literal cell, recalc() must update direct dependents.

    The broken variant caches the first evaluation and recalc() is a no-op,
    so get_value('C1') returns the stale result.
    """
    s = Sheet()
    s.set_value("A1", 2.0)
    s.set_value("B1", 3.0)
    s.set_formula("C1", "=A1+B1")
    # Trigger first evaluation
    _ = s.get_value("C1")  # should be 5.0

    # Update upstream
    s.set_value("A1", 10.0)
    s.recalc()

    # Must reflect updated value: 10 + 3 = 13
    result = s.get_value("C1")
    assert gu.close(result, 13.0), (
        f"Expected 13.0 after recalc (A1 changed to 10), got {result}. "
        "recalc() must re-evaluate dependent formulas."
    )


def test_recalc_propagates_chained():
    """After updating A1, recalc propagates through B1 (dep of A1) to C1 (dep of B1).

    The broken variant fails this because recalc() is a no-op.
    """
    s = Sheet()
    s.set_value("A1", 1.0)
    s.set_formula("B1", "=A1*2")    # B1 = 2.0
    s.set_formula("C1", "=B1+10")   # C1 = 12.0

    # Trigger initial evaluation
    assert gu.close(s.get_value("B1"), 2.0)
    assert gu.close(s.get_value("C1"), 12.0)

    # Update root
    s.set_value("A1", 5.0)
    s.recalc()

    # B1 should now be 10.0; C1 should now be 20.0
    b1 = s.get_value("B1")
    c1 = s.get_value("C1")
    assert gu.close(b1, 10.0), f"Expected B1=10.0 after recalc, got {b1}"
    assert gu.close(c1, 20.0), f"Expected C1=20.0 after recalc, got {c1}"


# ========================================================================== #
# Topological order test
# ========================================================================== #

def test_topological_order_valid():
    """cells_in_topological_order() must place dependencies before dependents."""
    s = Sheet()
    s.set_value("A1", 1.0)
    s.set_formula("B1", "=A1+1")
    s.set_formula("C1", "=B1+1")

    order = s.cells_in_topological_order()
    assert isinstance(order, list)
    # All cells must appear
    for cell in ("A1", "B1", "C1"):
        assert cell in order, f"{cell} missing from topological order"

    # A1 before B1, B1 before C1
    assert order.index("A1") < order.index("B1"), "A1 must come before B1"
    assert order.index("B1") < order.index("C1"), "B1 must come before C1"


# ========================================================================== #
# Cycle detection tests
# ========================================================================== #

def test_detect_cycle_false():
    """detect_cycle() returns False on an acyclic spreadsheet."""
    s = Sheet()
    s.set_value("A1", 1.0)
    s.set_formula("B1", "=A1+1")
    assert s.detect_cycle() is False


def test_detect_cycle_true():
    """detect_cycle() returns True when a cycle exists."""
    s = Sheet()
    s.set_formula("X1", "=Y1+1")
    s.set_formula("Y1", "=X1+1")
    assert s.detect_cycle() is True


def test_cycle_raises_on_get_value():
    """get_value() raises ValueError when a cycle is present."""
    s = Sheet()
    s.set_formula("X1", "=Y1+1")
    s.set_formula("Y1", "=X1+1")
    with pytest.raises(ValueError):
        s.get_value("X1")


def test_cycle_raises_on_recalc():
    """recalc() raises ValueError when a cycle is present."""
    s = Sheet()
    s.set_formula("P1", "=Q1*2")
    s.set_formula("Q1", "=P1+3")
    with pytest.raises(ValueError):
        s.recalc()


# ========================================================================== #
# Operator precedence tests
# ========================================================================== #

def test_operator_precedence():
    """* must bind tighter than +: =2+3*4 must equal 14.0, not 20.0."""
    s = Sheet()
    s.set_formula("A1", "=2+3*4")
    result = s.get_value("A1")
    assert gu.close(result, 14.0), (
        f"Expected 14.0 (2 + (3*4)), got {result}. Check operator precedence."
    )


def test_parentheses_override_prec():
    """Parentheses must override default precedence: =(2+3)*4 must equal 20.0."""
    s = Sheet()
    s.set_formula("A1", "=(2+3)*4")
    result = s.get_value("A1")
    assert gu.close(result, 20.0), (
        f"Expected 20.0 ((2+3)*4), got {result}. Check parenthesis handling."
    )


def test_division():
    """Division: =A1/B1 computes correct float result."""
    s = Sheet()
    s.set_value("A1", 10.0)
    s.set_value("B1", 4.0)
    s.set_formula("C1", "=A1/B1")
    result = s.get_value("C1")
    assert gu.close(result, 2.5), f"Expected 2.5, got {result}"


# ========================================================================== #
# Advisory code quality
# ========================================================================== #

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — prints code quality metrics but never fails the test."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
