"""Grader for swe_bench/swe04_unit_calc.

Tests the public contract:
    calc.parse(text) -> Quantity
    calc.to_dim(q)   -> dict
    ops.multiply / ops.divide / ops.add  (loaded directly for isolation)

Gold must PASS all tests; broken must FAIL >= 1 test.

FAIL-to-PASS tests (should fail on broken, pass on gold):
  - test_divide_dim_ms        m/s → s exponent is -1 not +1
  - test_divide_dim_ms2       (m/s)/s → s exponent is -2
  - test_divide_dimensionless m/m → empty dimension map
  - test_divide_magnitude_correct  magnitude of division is correct AND dim is correct

PASS-to-PASS tests (both gold and broken pass):
  - test_multiply_dims_add
  - test_add_same_unit_ok
  - test_add_incompatible_raises
  - test_magnitude_arithmetic
  - test_parse_single_quantity
  - test_to_dim_returns_copy

Mutation-corpus tests (oracle-grounded, independent evaluator):
  - test_mutation_corpus (parametrized, ~120 cases)
  - test_metamorphic_unit_cancel (10 cases: dim(a/b*b) == dim(a))
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "swe_bench", "swe04_unit_calc"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# ---------------------------------------------------------------------------
# Oracle-grounded mutation corpus (hidden under expected/, never shown to agent).
# Expected outputs come from an independent from-scratch dimensional-analysis
# evaluator (see experiment_mihaco/mutation_gen/gen_swe04_unit_calc.py).
# Cross-validated against the gold; every input kills >=1 wrong solution.
# ---------------------------------------------------------------------------
_CORPUS = json.loads(
    (Path(__file__).resolve().parents[1] / "expected" / "mutation_corpus.json").read_text()
)

# Load modules from the candidate solution directory.
# We need at least 2 modules loaded (ops + calc) to satisfy the multi-module requirement.
ops_mod = gu.load_module(SOL, "ops.py", alias="ops")
calc_mod = gu.load_module(SOL, "calc.py", alias="calc")

multiply = ops_mod.multiply
divide = ops_mod.divide
add = ops_mod.add
parse = calc_mod.parse
to_dim = calc_mod.to_dim


# ---------------------------------------------------------------------------
# Helper — build a Quantity via parse so we stay on the public contract
# ---------------------------------------------------------------------------

def qty(text: str):
    """Shorthand: parse a text expression and return the Quantity."""
    return parse(text)


# ---------------------------------------------------------------------------
# FAIL-to-PASS tests (broken variant must fail at least one of these)
# ---------------------------------------------------------------------------

def test_divide_dim_ms():
    """m / s must yield dimension {'m': 1, 's': -1}.

    The broken variant adds exponents instead of subtracting, producing
    {'m': 1, 's': 1}.  This is the primary discriminating test.
    """
    q = parse("1 m / 1 s")
    d = to_dim(q)
    assert d.get("m") == 1, f"Expected m:1, got {d}"
    assert d.get("s") == -1, f"Expected s:-1, got {d}"


def test_divide_dim_ms2():
    """(m/s)/s must yield dimension {'m': 1, 's': -2}."""
    q = parse("12 m / 2 s / 3 s")
    d = to_dim(q)
    assert d.get("m") == 1, f"Expected m:1, got {d}"
    assert d.get("s") == -2, f"Expected s:-2, got {d}"


def test_divide_dimensionless():
    """m / m must be dimensionless (empty dimension map) with magnitude 3."""
    q = parse("6 m / 2 m")
    d = to_dim(q)
    assert d == {}, f"Expected empty dim map (dimensionless), got {d}"
    assert gu.close(q.magnitude, 3.0), f"Expected magnitude 3.0, got {q.magnitude}"


def test_divide_magnitude_correct_and_dim_correct():
    """4 m / 2 s → magnitude 2.0 AND dimension {'m':1,'s':-1}."""
    q = parse("4 m / 2 s")
    assert gu.close(q.magnitude, 2.0), f"Expected magnitude 2.0, got {q.magnitude}"
    d = to_dim(q)
    assert d.get("m") == 1 and d.get("s") == -1, (
        f"Expected {{'m':1,'s':-1}}, got {d}"
    )


def test_divide_ops_direct():
    """Direct ops.divide call: m/s dimension must be {'m':1,'s':-1}.

    Uses the ops module directly (second-module path for grader integrity).
    """
    q_m = parse("1 m")
    q_s = parse("1 s")
    result = divide(q_m, q_s)
    d = to_dim(result)
    assert d.get("s") == -1, f"Expected s:-1 via ops.divide, got {d}"


# ---------------------------------------------------------------------------
# PASS-to-PASS tests (both gold and broken must pass these)
# ---------------------------------------------------------------------------

def test_multiply_dims_add():
    """Multiplying m * s must give dimension {'m':1, 's':1}."""
    q = parse("2 m * 3 s")
    d = to_dim(q)
    assert d.get("m") == 1, f"Expected m:1, got {d}"
    assert d.get("s") == 1, f"Expected s:1, got {d}"
    assert gu.close(q.magnitude, 6.0), f"Expected magnitude 6.0, got {q.magnitude}"


def test_add_same_unit_ok():
    """Adding two quantities with the same unit succeeds."""
    q1 = parse("3 m")
    q2 = parse("5 m")
    result = add(q1, q2)
    assert gu.close(result.magnitude, 8.0)
    d = to_dim(result)
    assert d.get("m") == 1, f"Expected m:1, got {d}"


def test_add_incompatible_raises():
    """Adding m + s must raise ValueError (incompatible units)."""
    q_m = parse("1 m")
    q_s = parse("1 s")
    with pytest.raises(ValueError):
        add(q_m, q_s)


def test_magnitude_arithmetic():
    """Scalar magnitude arithmetic is correct across multiply/divide."""
    q = parse("10 m / 2 s")
    assert gu.close(q.magnitude, 5.0), f"Expected 5.0, got {q.magnitude}"
    q2 = parse("3 m * 4 s")
    assert gu.close(q2.magnitude, 12.0), f"Expected 12.0, got {q2.magnitude}"


def test_parse_single_quantity():
    """parse('3 m') returns magnitude 3.0 and dimension {'m':1}."""
    q = parse("3 m")
    assert gu.close(q.magnitude, 3.0)
    assert to_dim(q) == {"m": 1}


def test_to_dim_returns_copy():
    """to_dim must return a copy; mutating it does not affect the Quantity."""
    q = parse("1 m")
    d = to_dim(q)
    d["m"] = 99   # mutate the returned dict
    # Original quantity must be unchanged
    assert to_dim(q) == {"m": 1}, "to_dim should return a copy, not a reference"


def test_parse_pure_number():
    """'5' with no unit → magnitude 5.0 and empty dimension map."""
    q = parse("5")
    assert gu.close(q.magnitude, 5.0)
    assert to_dim(q) == {}


def test_divide_kg_per_s():
    """kg / s must yield {'kg':1, 's':-1}."""
    q = parse("6 kg / 3 s")
    d = to_dim(q)
    assert d.get("kg") == 1, f"Expected kg:1, got {d}"
    assert d.get("s") == -1, f"Expected s:-1, got {d}"
    assert gu.close(q.magnitude, 2.0)


# ---------------------------------------------------------------------------
# Mutation-corpus test (oracle-grounded, ~120 cases)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", _CORPUS["cases"], ids=range(len(_CORPUS["cases"])))
def test_mutation_corpus(case):
    """Replay the oracle-grounded, mutation-seeded corpus.

    Expected outputs come from an independent from-scratch dimensional-analysis
    evaluator (structurally different from the gold), cross-validated against
    the gold.  Every input kills >=1 known wrong solution (the __broken
    division-adds variant or an AST mutant of ops.py).
    """
    (text,) = case["args"]
    expected = case["expected"]
    q = parse(text)
    dim = {k: v for k, v in to_dim(q).items() if v != 0}
    actual = {"mag": round(q.magnitude, 9), "dim": dict(sorted(dim.items()))}
    assert actual == expected, (
        f"parse({text!r}): expected {expected!r}, got {actual!r}"
    )


# ---------------------------------------------------------------------------
# Metamorphic test: dim((a) / (b) * (b)) == dim(a)  [units cancel]
# This breaks same-author circularity — no external oracle needed.
# ---------------------------------------------------------------------------

def _metamorphic_pairs(seed: int = 20260616, n: int = 10):
    """Generate (a, b) unit-expression pairs for the metamorphic relation."""
    rng = random.Random(seed)
    units = ["m", "s", "kg"]
    scalars = [1, 2, 3, 4, 6]
    pairs = []
    for _ in range(n):
        # a: scalar * unit
        a_val = rng.choice(scalars)
        a_unit = rng.choice(units)
        a = f"{a_val} {a_unit}"
        # b: scalar * unit (possibly different from a)
        b_val = rng.choice(scalars)
        b_unit = rng.choice(units)
        b = f"{b_val} {b_unit}"
        pairs.append((a, b))
    return pairs


_METAMORPHIC_PAIRS = _metamorphic_pairs()


@pytest.mark.parametrize("ab", _METAMORPHIC_PAIRS, ids=[f"meta{i}" for i in range(len(_METAMORPHIC_PAIRS))])
def test_metamorphic_unit_cancel(ab):
    """Metamorphic relation: dim((a) / (b) * (b)) == dim(a).

    Dividing then multiplying by the same quantity must restore the original
    unit (unit cancellation is the identity).  This test requires no external
    oracle; the candidate's own parse/to_dim results are compared against each
    other.  A broken divide (that adds exponents) will produce wrong dimensions
    in '(a) / (b)' so the subsequent '* (b)' will not cancel them correctly.
    """
    a_text, b_text = ab
    # dim of a alone
    qa = parse(a_text)
    dim_a = {k: v for k, v in to_dim(qa).items() if v != 0}

    # dim of (a) / (b) * (b) — should equal dim of (a)
    expr = f"{a_text} / {b_text} * {b_text}"
    q_combined = parse(expr)
    dim_combined = {k: v for k, v in to_dim(q_combined).items() if v != 0}

    assert dim_combined == dim_a, (
        f"Metamorphic check failed: dim('{expr}') = {dim_combined!r} "
        f"but dim('{a_text}') = {dim_a!r}  — unit cancellation broken"
    )


# ---------------------------------------------------------------------------
# Advisory code quality
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
