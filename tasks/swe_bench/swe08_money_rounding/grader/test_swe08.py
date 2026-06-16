"""Grader for swe_bench/swe08_money_rounding. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant has money.round_cents truncating toward zero instead of
rounding half-to-even, so lines whose exact per-line tax has a fractional part
above half a cent (and the 3.5 tie) come out one cent low — observed through
Invoice.tax_total / Invoice.total at the facade boundary.

All monetary comparisons are EXACT integer-cent equality (no floats compared).

Tests:
  PASS_TO_PASS (gold AND broken agree) — no rounding-up involved:
    1. test_subtotal_mixed_lines          — subtotal is pure unit*qty sum
    2. test_whole_cent_tax_line           — tax that is an exact whole cent (1000)
    3. test_tie_two_point_five_even_down  — 2.5 -> 2 (even); trunc agrees
    4. test_format_cents_values           — "$X.YY" formatter for several values
    5. test_empty_invoice_totals_zero     — empty invoice totals are 0

  FAIL_TO_PASS (gold true, broken false) — rounding must round up:
    6. test_round_cents_rounds_up_fraction    — round_cents(493.7625) -> 494
    7. test_round_cents_tie_half_to_even_up    — round_cents(3.5) -> 4
    8. test_line_tax_rounds_up                 — line_tax(5985, 0.0825) -> 494
    9. test_invoice_tax_total_and_total        — facade tax_total/total reflect 494
   10. test_multi_line_tax_total_per_line      — per-line rounding then sum

  Advisory:
   11. test_code_quality_report
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "swe_bench", "swe08_money_rounding"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load all three modules separately (3-module mini-repo).
_money_mod = gu.load_module(SOL, "money.py", alias="money")
_tax_mod = gu.load_module(SOL, "tax.py", alias="tax")
_invoice_mod = gu.load_module(SOL, "invoice.py", alias="invoice")

round_cents = getattr(_money_mod, "round_cents")
line_tax = getattr(_tax_mod, "line_tax")
Invoice = getattr(_invoice_mod, "Invoice")
format_cents = getattr(_invoice_mod, "format_cents")


# ===========================================================================
# PASS_TO_PASS tests — truncation and rounding agree here
# ===========================================================================

def test_subtotal_mixed_lines():
    """Subtotal is the pure sum of unit_price_cents * qty (no rounding)."""
    inv = Invoice()
    inv.add_line("widget", 1995, 3, 0.0825)   # 5985
    inv.add_line("gadget", 1000, 2, 0.10)     # 2000
    inv.add_line("gizmo", 333, 1, 0.05)       # 333
    assert inv.subtotal() == 5985 + 2000 + 333


def test_whole_cent_tax_line():
    """A line whose exact tax is already a whole number of cents.

    10000 cents * 0.10 = 1000.00 cents exactly -> 1000 by rounding OR truncation.
    """
    assert line_tax(10000, 0.10) == 1000
    inv = Invoice()
    inv.add_line("flat", 10000, 1, 0.10)
    assert inv.subtotal() == 10000
    assert inv.tax_total() == 1000
    assert inv.total() == 11000


def test_tie_two_point_five_even_down():
    """An exact .5 tie that rounds to the even neighbour DOWN: 2.5 -> 2.

    Truncation also yields 2, so gold and broken agree on this case.
    Reached via line_tax too: 50 cents * 0.05 = 2.50 cents -> 2.
    """
    assert round_cents(Decimal("2.5")) == 2
    assert line_tax(50, 0.05) == 2


def test_format_cents_values():
    """The "$X.YY" formatter renders integer cents correctly."""
    assert format_cents(0) == "$0.00"
    assert format_cents(5) == "$0.05"
    assert format_cents(99) == "$0.99"
    assert format_cents(100) == "$1.00"
    assert format_cents(494) == "$4.94"
    assert format_cents(123456) == "$1234.56"


def test_empty_invoice_totals_zero():
    """An invoice with no lines totals to zero on every accessor."""
    inv = Invoice()
    assert inv.subtotal() == 0
    assert inv.tax_total() == 0
    assert inv.total() == 0


# ===========================================================================
# FAIL_TO_PASS tests — broken truncation gives a cent too few
# ===========================================================================

def test_round_cents_rounds_up_fraction():
    """Fractional part > 0.5 cent must round UP: 493.7625 -> 494.

    Broken truncates to 493.
    """
    assert round_cents(Decimal("493.7625")) == 494


def test_round_cents_tie_half_to_even_up():
    """Exact .5 tie whose even neighbour is UP: 3.5 -> 4.

    Broken truncates to 3.  (2.5 -> 2 is asserted in PASS_TO_PASS; only the
    tie that the half-to-even rule actually fixes is checked here.)
    """
    assert round_cents(Decimal("3.5")) == 4


def test_line_tax_rounds_up():
    """line_tax must round the exact per-line tax, not truncate it.

    5985 cents * 0.0825 = 493.7625 cents -> 494 (broken: 493).
    Also a tie reached through line_tax: 70 cents * 0.05 = 3.50 -> 4 (broken: 3).
    """
    assert line_tax(5985, 0.0825) == 494
    assert line_tax(70, 0.05) == 4


def test_invoice_tax_total_and_total():
    """Facade symptom: tax_total / total reflect the ROUNDED per-line tax.

    Single line 1995 * 3 = 5985 cents at 0.0825 -> tax 494 -> total 6479.
    Broken yields tax_total 493 and total 6478 (a cent low).
    """
    inv = Invoice()
    inv.add_line("widget", 1995, 3, 0.0825)
    assert inv.subtotal() == 5985
    assert inv.tax_total() == 494
    assert inv.total() == 5985 + 494


def test_multi_line_tax_total_per_line():
    """Tax is computed PER LINE (each rounded) then summed.

    Line A: 5985 @ 0.0825 -> 493.7625 -> 494
    Line B:   70 @ 0.05    ->   3.50   ->   4  (tie rounds to even = up)
    Line C: 10000 @ 0.10   -> 1000.00  -> 1000 (whole cent, agrees)
    Gold tax_total = 494 + 4 + 1000 = 1498.  Broken = 493 + 3 + 1000 = 1496.
    """
    inv = Invoice()
    inv.add_line("a", 5985, 1, 0.0825)
    inv.add_line("b", 70, 1, 0.05)
    inv.add_line("c", 10000, 1, 0.10)
    assert inv.subtotal() == 5985 + 70 + 10000
    assert inv.tax_total() == 494 + 4 + 1000
    assert inv.total() == (5985 + 70 + 10000) + (494 + 4 + 1000)


# ===========================================================================
# Advisory code quality
# ===========================================================================

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
