"""Grader for harness/h04_expr_eval.

Tests the public contract only (see TASK.md): ``evaluate(expr) -> float``.
Validity invariant: PASSES on the gold reference (all tests), FAILS on the
deliberately-broken reference (>=1 test).

The broken reference parses ``**`` as LEFT-associative (so
``evaluate("2 ** 3 ** 2") == 64.0`` instead of ``512.0``) while everything else
— binary ``+ - * /`` precedence and associativity, the unary-vs-power
precedence (``-2 ** 2 == -4``), parentheses, decimals, and the exception
contract — stays correct. The right-associativity tests below
(``test_power_right_associative`` and the matching ``oracle`` rows) are the
FAIL_TO_PASS that kill that defect; the basic-arithmetic, precedence,
parenthesis and exception tests still pass on the broken variant.

Grounding: the expected values for the oracle cases are computed BY HAND in this
grader from the precedence rules in TASK.md (right-associative ``**`` that binds
tighter than unary minus, true division), NOT by importing the gold reference.
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h04_expr_eval"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

evaluate = gu.load_callable(SOL, "solution.py", "evaluate")


# ---------------------------------------------------------------------------
# Test 1: basic binary arithmetic and left-to-right associativity of + - * /.
# ---------------------------------------------------------------------------
def test_basic_arithmetic_and_left_assoc():
    assert gu.close(evaluate("1 + 2 * 3"), 7.0)          # * binds tighter than +
    assert gu.close(evaluate("2 - 3 - 4"), -5.0)         # left-assoc: (2-3)-4
    assert gu.close(evaluate("8 / 2 / 2"), 2.0)          # left-assoc: (8/2)/2
    assert gu.close(evaluate("2 + 3 * 4 - 1"), 13.0)
    assert gu.close(evaluate("100 / 10 / 5"), 2.0)


# ---------------------------------------------------------------------------
# Test 2: '/' is TRUE division and always yields a non-integer where expected.
# ---------------------------------------------------------------------------
def test_true_division():
    assert gu.close(evaluate("10 / 4"), 2.5)             # not floor division
    assert gu.close(evaluate("7 / 2"), 3.5)
    assert gu.close(evaluate("1 / 8"), 0.125)


# ---------------------------------------------------------------------------
# Test 3: parentheses override precedence; nesting is respected.
# ---------------------------------------------------------------------------
def test_parentheses():
    assert gu.close(evaluate("(1 + 2) * 3"), 9.0)
    assert gu.close(evaluate("2 * (3 + 4)"), 14.0)
    assert gu.close(evaluate("((2))"), 2.0)
    assert gu.close(evaluate("(2 + 3) * (4 - 1)"), 15.0)
    assert gu.close(evaluate("-(3 + 4)"), -7.0)


# ---------------------------------------------------------------------------
# Test 4: unary +/- chains.
# ---------------------------------------------------------------------------
def test_unary_chains():
    assert gu.close(evaluate("--3"), 3.0)                # double negation
    assert gu.close(evaluate("-3"), -3.0)
    assert gu.close(evaluate("+3"), 3.0)
    assert gu.close(evaluate("---3"), -3.0)              # odd count -> negative
    assert gu.close(evaluate("3 * -2"), -6.0)            # unary minus as an operand
    assert gu.close(evaluate("3 - -2"), 5.0)


# ---------------------------------------------------------------------------
# Test 5: decimal and edge numeric literals (.5, 2., 3.5).
# ---------------------------------------------------------------------------
def test_decimal_literals():
    assert gu.close(evaluate(".5 + 2."), 2.5)            # leading- and trailing-dot literals
    assert gu.close(evaluate("12 + 3.5"), 15.5)
    assert gu.close(evaluate("2. * .5"), 1.0)
    assert gu.close(evaluate("0.125 + 0.875"), 1.0)


# ---------------------------------------------------------------------------
# Test 6 [FAIL_TO_PASS]: '**' is RIGHT-associative.
#   2 ** 3 ** 2 == 2 ** (3 ** 2) == 2 ** 9 == 512   (NOT (2**3)**2 == 64)
#   2 ** 2 ** 3 == 2 ** (2 ** 3) == 2 ** 8 == 256   (NOT (2**2)**3 == 64)
# The broken (left-assoc) reference returns 64.0 for both, so this fails it.
# ---------------------------------------------------------------------------
def test_power_right_associative():
    assert gu.close(evaluate("2 ** 3 ** 2"), 512.0)
    assert gu.close(evaluate("2 ** 2 ** 3"), 256.0)
    # A three-deep chain to nail down the association: 2**(1**(2**3)) == 2.
    assert gu.close(evaluate("2 ** 1 ** 2 ** 3"), 2.0)


# ---------------------------------------------------------------------------
# Test 7 [FAIL_TO_PASS]: unary minus is LOOSER than '**', but a unary sign is
# still allowed as the exponent's operand.
#   -2 ** 2  == -(2 ** 2)   == -4     (unary minus applies to the whole power)
#   2 ** -2  == 2 ** (-2)   == 0.25   (unary minus IS allowed in the exponent)
#   -2 ** -2 == -(2 ** -2)  == -0.25
# ---------------------------------------------------------------------------
def test_unary_vs_power_precedence():
    assert gu.close(evaluate("-2 ** 2"), -4.0)
    assert gu.close(evaluate("2 ** -2"), 0.25)
    assert gu.close(evaluate("-2 ** -2"), -0.25)
    # Parenthesised base flips the precedence: (-2) ** 2 == 4.
    assert gu.close(evaluate("(-2) ** 2"), 4.0)


# ---------------------------------------------------------------------------
# Test 8: power composes with the other operators at the right precedence.
#   2 ** 3 * 2 == (2**3) * 2 == 16   (** binds tighter than *)
#   2 * 3 ** 2 == 2 * (3**2) == 18
# ---------------------------------------------------------------------------
def test_power_precedence_with_mul():
    assert gu.close(evaluate("2 ** 3 * 2"), 16.0)
    assert gu.close(evaluate("2 * 3 ** 2"), 18.0)
    assert gu.close(evaluate("1 + 2 ** 3"), 9.0)


# ---------------------------------------------------------------------------
# Test 9: the result is ALWAYS a Python float.
# ---------------------------------------------------------------------------
def test_result_is_float():
    for expr in ["1 + 1", "2 ** 3", "6 / 2", "(4)", "-5", "10 - 4 * 2"]:
        result = evaluate(expr)
        assert isinstance(result, float), f"{expr!r} -> {result!r} ({type(result).__name__})"


# ---------------------------------------------------------------------------
# Test 10: ZeroDivisionError on division by zero and 0 ** negative.
# ---------------------------------------------------------------------------
def test_zero_division():
    with pytest.raises(ZeroDivisionError):
        evaluate("1 / 0")
    with pytest.raises(ZeroDivisionError):
        evaluate("0 ** -1")
    with pytest.raises(ZeroDivisionError):
        evaluate("5 / (2 - 2)")          # divisor evaluates to zero
    with pytest.raises(ZeroDivisionError):
        evaluate("0 ** -2")


# ---------------------------------------------------------------------------
# Test 11: ValueError on a variety of malformed expressions.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "bad",
    [
        "",            # empty
        "   ",         # blank
        "(",           # unbalanced (open)
        "(1 + 2",      # unbalanced (open)
        "1 + 2)",      # unbalanced (close)
        ")",           # stray close
        "()",          # empty parentheses (missing operand)
        "1 +",         # trailing operator (missing operand)
        "* 3",         # leading binary operator (missing operand)
        "** 3",        # leading '**' (missing operand)
        "2 **",        # trailing '**' (missing operand)
        "1 2",         # two juxtaposed literals (no operator)
        "1 +* 2",      # two adjacent binary operators
        "3 $ 4",       # unknown character
        ".",           # lone dot is not a literal
        "1..2",        # malformed numeric literal (two dots)
    ],
)
def test_malformed_raises_valueerror(bad):
    with pytest.raises(ValueError):
        evaluate(bad)


# ---------------------------------------------------------------------------
# Test 12 [FAIL_TO_PASS]: INDEPENDENT ORACLE.
# Expected values are computed BY HAND here from the precedence rules in TASK.md
# (right-associative '**' that binds tighter than unary minus; left-associative
# + - * /; true division) — they are NOT obtained by importing the gold. Several
# rows exercise right-associativity / unary-vs-power, so this also kills the
# left-associative '**' defect.
# ---------------------------------------------------------------------------
_ORACLE_CASES = [
    # (expression, hand-computed expected float, derivation)
    ("2 ** 3 ** 2", 512.0, "2 ** (3 ** 2) = 2 ** 9"),
    ("2 ** 2 ** 3", 256.0, "2 ** (2 ** 3) = 2 ** 8"),
    ("-2 ** 2", -4.0, "-(2 ** 2)"),
    ("2 ** -2", 0.25, "2 ** (-2)"),
    ("-2 ** -2", -0.25, "-(2 ** (-2))"),
    ("1 + 2 * 3", 7.0, "1 + (2*3)"),
    ("8 / 2 / 2", 2.0, "(8/2)/2"),
    ("(1 + 2) * 3", 9.0, "3 * 3"),
    ("10 / 4", 2.5, "true division"),
    ("2 ** 3 * 2", 16.0, "(2**3) * 2"),
    ("--3", 3.0, "-(-3)"),
    (".5 + 2.", 2.5, "0.5 + 2.0"),
]


@pytest.mark.parametrize("expr,expected,_why", _ORACLE_CASES)
def test_against_hand_built_oracle(expr, expected, _why):
    got = evaluate(expr)
    assert isinstance(got, float)
    assert gu.close(got, expected), f"{expr!r} -> {got!r}, expected {expected!r} ({_why})"


# ---------------------------------------------------------------------------
# Test 13: whitespace is insignificant — spacing must not change the value.
# ---------------------------------------------------------------------------
def test_whitespace_insignificant():
    assert gu.close(evaluate("1+2*3"), evaluate("  1  +  2  *  3  "))
    assert gu.close(evaluate("2**3**2"), 512.0)          # no spaces, still right-assoc
    assert gu.close(evaluate("\t-2 ** 2\n"), -4.0)


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail).
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
