"""Generate the oracle-grounded mutation corpus for swe_bench/swe04_unit_calc.

Independent oracle: a from-scratch dimensional-analysis evaluator that
tokenizes "A op B [op C...]" expressions with units in {m, s, kg} and numeric
scalars.  Multiply ADDS exponents; DIVIDE NEGATES the divisor's exponents and
SUBTRACTS; magnitudes are combined accordingly.  The oracle is structurally
independent of the gold (no shared code).

Provenance: "Dimensional analysis: division does not negate unit exponents —
cf. pint issue #301. Grader ground truth: independent evaluator + metamorphic
relation (a/b)*b == a."

Run:  python3 experiment_mihaco/mutation_gen/gen_swe04_unit_calc.py
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu   # noqa: E402
import _mutation_seed as ms            # noqa: E402

CATEGORY, TASK_ID = "swe_bench", "swe04_unit_calc"
GOLD_DIR   = gu.GOLD_ROOT / CATEGORY / TASK_ID
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / f"{TASK_ID}__broken"

# Source texts for multi-module package loading
_UNITS_SRC  = (GOLD_DIR / "units.py").read_text()
_OPS_SRC    = (GOLD_DIR / "ops.py").read_text()
_CALC_SRC   = (GOLD_DIR / "calc.py").read_text()

_BROKEN_UNITS_SRC  = (BROKEN_DIR / "units.py").read_text()
_BROKEN_OPS_SRC    = (BROKEN_DIR / "ops.py").read_text()
_BROKEN_CALC_SRC   = (BROKEN_DIR / "calc.py").read_text()

# ---------------------------------------------------------------------------
# Gold: load parse + to_dim from the gold package, wrap in eval_expr
# ---------------------------------------------------------------------------
_gold_calc_mod = gu.load_module(GOLD_DIR, "calc.py", alias="gold_calc_swe04")
_gold_parse  = _gold_calc_mod.parse
_gold_to_dim = _gold_calc_mod.to_dim


def _normalize_dim(d: dict) -> dict:
    """Keep only non-zero exponents, keys sorted."""
    return {k: v for k, v in sorted(d.items()) if v != 0}


def gold(text: str) -> dict:
    q = _gold_parse(text)
    d = _gold_to_dim(q)
    return {"mag": round(q.magnitude, 9), "dim": _normalize_dim(d)}


# ---------------------------------------------------------------------------
# Independent oracle: from-scratch dimensional evaluator
# ---------------------------------------------------------------------------
_BASE_UNITS = {"m", "s", "kg"}
_TOKEN_RE = re.compile(
    r"(?P<num>-?\d+(?:\.\d+)?)|(?P<unit>[a-zA-Z]+)|(?P<op>[*/])"
)


def _oracle_tokenize(text: str):
    tokens = []
    for m in _TOKEN_RE.finditer(text):
        if m.lastgroup == "num":
            tokens.append(("num", float(m.group())))
        elif m.lastgroup == "unit":
            tokens.append(("unit", m.group()))
        elif m.lastgroup == "op":
            tokens.append(("op", m.group()))
    return tokens


def _oracle_parse_atom(tokens, pos):
    """Parse one (num [unit]) atom, return ((mag, dims), new_pos)."""
    tok_type, tok_val = tokens[pos]
    assert tok_type == "num", f"expected num at {pos}, got {tok_type}"
    mag = tok_val
    pos += 1
    dims: dict[str, int] = {}
    if pos < len(tokens) and tokens[pos][0] == "unit":
        unit = tokens[pos][1]
        dims = {unit: 1}
        pos += 1
    return (mag, dims), pos


def oracle(text: str) -> dict:
    """Independent from-scratch dimensional-analysis evaluator."""
    tokens = _oracle_tokenize(text.strip())
    if not tokens:
        return {"mag": 0.0, "dim": {}}

    (mag, dims), pos = _oracle_parse_atom(tokens, 0)

    while pos < len(tokens):
        tok_type, tok_val = tokens[pos]
        if tok_type != "op":
            break
        op = tok_val
        pos += 1
        (rhs_mag, rhs_dims), pos = _oracle_parse_atom(tokens, pos)

        if op == "*":
            mag = mag * rhs_mag
            new_dims = dict(dims)
            for unit, exp in rhs_dims.items():
                new_dims[unit] = new_dims.get(unit, 0) + exp
            dims = {k: v for k, v in new_dims.items() if v != 0}
        elif op == "/":
            mag = mag / rhs_mag
            new_dims = dict(dims)
            for unit, exp in rhs_dims.items():
                # DIVIDE: subtract (negate) the divisor's exponents
                new_dims[unit] = new_dims.get(unit, 0) - exp
            dims = {k: v for k, v in new_dims.items() if v != 0}

    return {"mag": round(mag, 9), "dim": _normalize_dim(dims)}


# ---------------------------------------------------------------------------
# Wrong functions
# ---------------------------------------------------------------------------

def _make_gold_eval_from_package(files: dict, alias_prefix: str) -> callable:
    """Load a variant calc module and wrap parse+to_dim into eval_expr."""
    import importlib.util, sys, tempfile, uuid
    from pathlib import Path as _P
    d = _P(tempfile.mkdtemp(prefix="mutpkg_"))
    for fname, src in files.items():
        (d / fname).write_text(src)
    sys.path.insert(0, str(d))
    try:
        modname = f"{alias_prefix}_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(modname, d / "calc.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _parse = mod.parse
        _to_dim = mod.to_dim
        def _eval(text: str) -> dict:
            q = _parse(text)
            d2 = _to_dim(q)
            return {"mag": round(q.magnitude, 9), "dim": _normalize_dim(d2)}
        return _eval
    finally:
        if str(d) in sys.path:
            sys.path.remove(str(d))


def _wrong_fns():
    wrongs = []

    # 1. The real __broken (division adds exponents)
    try:
        broken_eval = _make_gold_eval_from_package(
            {"units.py": _BROKEN_UNITS_SRC,
             "ops.py":   _BROKEN_OPS_SRC,
             "calc.py":  _BROKEN_CALC_SRC},
            alias_prefix="broken_swe04"
        )
        wrongs.append(("__broken", broken_eval))
    except Exception as e:
        print(f"Warning: could not load __broken: {e}")

    # 2. AST mutants of ops.py (the buggy module), other modules unchanged
    for label, mutant_ops in ms.generate_mutants(_OPS_SRC):
        try:
            fn = _make_gold_eval_from_package(
                {"units.py": _UNITS_SRC,
                 "ops.py":   mutant_ops,
                 "calc.py":  _CALC_SRC},
                alias_prefix=f"mut_swe04_{label}"
            )
            wrongs.append((label, fn))
        except Exception:
            continue

    # 3. Hand-written wrong solutions

    # Wrong A: division that ADDS exponents (same bug as __broken but standalone)
    _wrong_a_src = """
import re
def _tok(text):
    TR = re.compile(r'(?P<num>-?\\d+(?:\\.\\d+)?)|(?P<unit>[a-zA-Z]+)|(?P<op>[*/])')
    toks = []
    for m in TR.finditer(text):
        if m.lastgroup == 'num': toks.append(('num', float(m.group())))
        elif m.lastgroup == 'unit': toks.append(('unit', m.group()))
        elif m.lastgroup == 'op': toks.append(('op', m.group()))
    return toks

def _atom(toks, pos):
    mag = toks[pos][1]; pos += 1
    dims = {}
    if pos < len(toks) and toks[pos][0] == 'unit':
        dims = {toks[pos][1]: 1}; pos += 1
    return (mag, dims), pos

def wrong_divide_adds(text):
    toks = _tok(text.strip())
    if not toks: return {'mag': 0.0, 'dim': {}}
    (mag, dims), pos = _atom(toks, 0)
    while pos < len(toks):
        if toks[pos][0] != 'op': break
        op = toks[pos][1]; pos += 1
        (rmag, rdims), pos = _atom(toks, pos)
        if op == '*':
            mag *= rmag
            for u, e in rdims.items(): dims[u] = dims.get(u,0)+e
        elif op == '/':
            mag /= rmag
            # BUG: add instead of subtract
            for u, e in rdims.items(): dims[u] = dims.get(u,0)+e
        dims = {k:v for k,v in dims.items() if v != 0}
    return {'mag': round(mag, 9), 'dim': {k:v for k,v in sorted(dims.items()) if v != 0}}
"""
    try:
        fn_a = ms.load_callable_from_source(_wrong_a_src, "wrong_divide_adds")
        wrongs.append(("hand_divide_adds", fn_a))
    except Exception as e:
        print(f"Warning: hand_divide_adds failed: {e}")

    # Wrong B: division that leaves exponents unchanged (does not modify dims)
    _wrong_b_src = """
import re
def _tok(text):
    TR = re.compile(r'(?P<num>-?\\d+(?:\\.\\d+)?)|(?P<unit>[a-zA-Z]+)|(?P<op>[*/])')
    toks = []
    for m in TR.finditer(text):
        if m.lastgroup == 'num': toks.append(('num', float(m.group())))
        elif m.lastgroup == 'unit': toks.append(('unit', m.group()))
        elif m.lastgroup == 'op': toks.append(('op', m.group()))
    return toks

def _atom(toks, pos):
    mag = toks[pos][1]; pos += 1
    dims = {}
    if pos < len(toks) and toks[pos][0] == 'unit':
        dims = {toks[pos][1]: 1}; pos += 1
    return (mag, dims), pos

def wrong_divide_unchanged(text):
    toks = _tok(text.strip())
    if not toks: return {'mag': 0.0, 'dim': {}}
    (mag, dims), pos = _atom(toks, 0)
    while pos < len(toks):
        if toks[pos][0] != 'op': break
        op = toks[pos][1]; pos += 1
        (rmag, rdims), pos = _atom(toks, pos)
        if op == '*':
            mag *= rmag
            for u, e in rdims.items(): dims[u] = dims.get(u,0)+e
        elif op == '/':
            mag /= rmag
            # BUG: do not modify dims at all
            pass
        dims = {k:v for k,v in dims.items() if v != 0}
    return {'mag': round(mag, 9), 'dim': {k:v for k,v in sorted(dims.items()) if v != 0}}
"""
    try:
        fn_b = ms.load_callable_from_source(_wrong_b_src, "wrong_divide_unchanged")
        wrongs.append(("hand_divide_unchanged", fn_b))
    except Exception as e:
        print(f"Warning: hand_divide_unchanged failed: {e}")

    # Wrong C: multiply that SUBTRACTS exponents
    _wrong_c_src = """
import re
def _tok(text):
    TR = re.compile(r'(?P<num>-?\\d+(?:\\.\\d+)?)|(?P<unit>[a-zA-Z]+)|(?P<op>[*/])')
    toks = []
    for m in TR.finditer(text):
        if m.lastgroup == 'num': toks.append(('num', float(m.group())))
        elif m.lastgroup == 'unit': toks.append(('unit', m.group()))
        elif m.lastgroup == 'op': toks.append(('op', m.group()))
    return toks

def _atom(toks, pos):
    mag = toks[pos][1]; pos += 1
    dims = {}
    if pos < len(toks) and toks[pos][0] == 'unit':
        dims = {toks[pos][1]: 1}; pos += 1
    return (mag, dims), pos

def wrong_multiply_subtracts(text):
    toks = _tok(text.strip())
    if not toks: return {'mag': 0.0, 'dim': {}}
    (mag, dims), pos = _atom(toks, 0)
    while pos < len(toks):
        if toks[pos][0] != 'op': break
        op = toks[pos][1]; pos += 1
        (rmag, rdims), pos = _atom(toks, pos)
        if op == '*':
            mag *= rmag
            # BUG: subtract instead of add
            for u, e in rdims.items(): dims[u] = dims.get(u,0)-e
        elif op == '/':
            mag /= rmag
            for u, e in rdims.items(): dims[u] = dims.get(u,0)-e
        dims = {k:v for k,v in dims.items() if v != 0}
    return {'mag': round(mag, 9), 'dim': {k:v for k,v in sorted(dims.items()) if v != 0}}
"""
    try:
        fn_c = ms.load_callable_from_source(_wrong_c_src, "wrong_multiply_subtracts")
        wrongs.append(("hand_multiply_subtracts", fn_c))
    except Exception as e:
        print(f"Warning: hand_multiply_subtracts failed: {e}")

    # Wrong D: off-by-one — divide negates but also adds 1 to divisor exponent
    _wrong_d_src = """
import re
def _tok(text):
    TR = re.compile(r'(?P<num>-?\\d+(?:\\.\\d+)?)|(?P<unit>[a-zA-Z]+)|(?P<op>[*/])')
    toks = []
    for m in TR.finditer(text):
        if m.lastgroup == 'num': toks.append(('num', float(m.group())))
        elif m.lastgroup == 'unit': toks.append(('unit', m.group()))
        elif m.lastgroup == 'op': toks.append(('op', m.group()))
    return toks

def _atom(toks, pos):
    mag = toks[pos][1]; pos += 1
    dims = {}
    if pos < len(toks) and toks[pos][0] == 'unit':
        dims = {toks[pos][1]: 1}; pos += 1
    return (mag, dims), pos

def wrong_divide_off_by_one(text):
    toks = _tok(text.strip())
    if not toks: return {'mag': 0.0, 'dim': {}}
    (mag, dims), pos = _atom(toks, 0)
    while pos < len(toks):
        if toks[pos][0] != 'op': break
        op = toks[pos][1]; pos += 1
        (rmag, rdims), pos = _atom(toks, pos)
        if op == '*':
            mag *= rmag
            for u, e in rdims.items(): dims[u] = dims.get(u,0)+e
        elif op == '/':
            mag /= rmag
            # BUG: negate + 1 (off by one)
            for u, e in rdims.items(): dims[u] = dims.get(u,0) - e + 1
        dims = {k:v for k,v in dims.items() if v != 0}
    return {'mag': round(mag, 9), 'dim': {k:v for k,v in sorted(dims.items()) if v != 0}}
"""
    try:
        fn_d = ms.load_callable_from_source(_wrong_d_src, "wrong_divide_off_by_one")
        wrongs.append(("hand_divide_off_by_one", fn_d))
    except Exception as e:
        print(f"Warning: hand_divide_off_by_one failed: {e}")

    return wrongs


# ---------------------------------------------------------------------------
# Input generator (seed 20260616)
# ---------------------------------------------------------------------------
_RNG = random.Random(20260616)
_UNITS = ["m", "s", "kg"]
_OPS = ["*", "/"]


def _rand_scalar() -> str:
    """Return a non-zero positive float as string."""
    val = _RNG.choice([1, 2, 3, 4, 6, 8, 10, 12, 0.5, 1.5, 2.5])
    return str(int(val)) if isinstance(val, int) else str(val)


def _rand_atom(allow_no_unit: bool = True) -> str:
    """Return 'scalar [unit]' or just 'scalar'."""
    scalar = _rand_scalar()
    if allow_no_unit and _RNG.random() < 0.2:
        return scalar
    unit = _RNG.choice(_UNITS)
    return f"{scalar} {unit}"


def _rand_expr(n_operands: int = None) -> str:
    """Random expression with 1-3 operands."""
    if n_operands is None:
        n_operands = _RNG.randint(1, 3)
    parts = [_rand_atom()]
    for _ in range(n_operands - 1):
        op = _RNG.choice(_OPS)
        parts.append(op)
        parts.append(_rand_atom(allow_no_unit=True))
    return " ".join(parts)


def _inputs():
    out = []

    # Fixed high-value edge cases from the spec
    out += [
        ("1 m / 1 s",),         # basic m/s
        ("4 m / 2 s",),         # magnitude + dim
        ("12 m / 2 s / 3 s",),  # chained division  → m/s²
        ("6 m / 2 m",),         # dimensionless cancel
        ("5",),                  # pure number
        ("3 m",),                # single unit
        ("2 m * 3 s",),         # multiply
        ("6 kg / 3 s",),        # kg/s
        ("1 kg * 1 m / 1 s",),  # kg·m/s (momentum)
        ("1 m / 1 s / 1 s",),   # m/s²
        ("1 kg * 1 m",),        # kg·m
        ("1 s / 1 m",),         # s/m (reciprocal)
        ("2 kg / 1 kg",),       # dimensionless via kg cancellation
        ("1 m * 1 m",),         # m² (area)
        ("10 m / 2 s",),
        ("3 m * 4 s",),
        ("1 m / 1 m / 1 m",),  # 1/m — tricky dimension
        ("6 m / 2 s / 1 m",),  # m/s/m = 1/s
        ("2 kg * 3 m / 6 s",), # kg·m/s
        ("1 s * 1 s",),         # s²
        ("4 m / 2",),           # scalar divisor (no unit)
        ("6 / 2 m",),           # scalar dividend (no unit)
        ("1 kg / 1 s / 1 s",), # kg/s²
    ]

    # Random expressions
    for _ in range(2000):
        out.append((_rand_expr(),))

    # Random 2-operand expressions (heavier weight)
    for _ in range(500):
        out.append((_rand_expr(n_operands=2),))

    # Random 3-operand expressions
    for _ in range(500):
        out.append((_rand_expr(n_operands=3),))

    return out


def main() -> int:
    wrongs = _wrong_fns()
    print(f"wrong_fns loaded: {len(wrongs)}")

    # Filter inputs that would cause division by zero or parser error
    safe = []
    for args in _inputs():
        text = args[0]
        try:
            result_g = gold(text)
            result_o = oracle(text)
        except Exception:
            continue
        safe.append(args)

    print(f"safe inputs: {len(safe)}")

    corpus = ms.build_corpus(
        gold,
        oracle,
        wrongs,
        safe,
        normalize=lambda x: x,   # identity — dict already normalized
        max_keep=120,
    )
    out = ms.write_corpus(
        ROOT / "tasks" / CATEGORY / TASK_ID,
        corpus,
        meta_extra={
            "oracle": "independent-reference+metamorphic",
            "provenance": (
                "Dimensional analysis: division does not negate unit exponents — "
                "cf. pint issue #301. Grader ground truth: independent evaluator + "
                "metamorphic relation (a/b)*b == a."
            ),
            "input_seed": 20260616,
        },
    )
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
