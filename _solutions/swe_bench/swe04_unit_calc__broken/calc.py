"""calc.py — Facade: parse a dimensional expression and inspect dimensions.

Public API:
    parse(text: str) -> Quantity
    to_dim(q: Quantity) -> dict
"""
from __future__ import annotations

import re
from typing import Dict

from units import Quantity
from ops import multiply, divide


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(text: str) -> Quantity:
    """Parse a dimensional expression and return a Quantity.

    Supported syntax (white-space around operators is flexible):
        "3 m"           → Quantity(3.0, {'m': 1})
        "2 m * 3 s"     → Quantity(6.0, {'m': 1, 's': 1})
        "4 m / 2 s"     → Quantity(2.0, {'m': 1, 's': -1})
        "12 m / 2 s / 3 s"  → Quantity(2.0, {'m': 1, 's': -2})
        "6 m / 2 m"     → Quantity(3.0, {})      # dimensionless
        "5"             → Quantity(5.0, {})       # pure number
    """
    tokens = _tokenize(text.strip())
    return _parse_expr(tokens)


def to_dim(q: Quantity) -> Dict[str, int]:
    """Return a copy of the dimension map of *q*.

    Keys with exponent 0 are omitted. The result maps base-unit symbol
    (e.g. 'm', 's', 'kg') to its integer exponent.
    """
    return q.dim_map()


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------
_BASE_UNITS = {"m", "s", "kg"}
_TOKEN_RE = re.compile(
    r"""
    (?P<num>-?\d+(?:\.\d+)?)   # integer or float (optionally negative)
    |(?P<unit>[a-zA-Z]+)        # unit symbol
    |(?P<op>[*/])               # operator
    """,
    re.VERBOSE,
)


def _tokenize(text: str):
    """Split *text* into a flat list of (type, value) pairs."""
    tokens = []
    for m in _TOKEN_RE.finditer(text):
        if m.lastgroup == "num":
            tokens.append(("num", float(m.group())))
        elif m.lastgroup == "unit":
            tokens.append(("unit", m.group()))
        elif m.lastgroup == "op":
            tokens.append(("op", m.group()))
    return tokens


# ---------------------------------------------------------------------------
# Parser — left-to-right, handles "num [unit] (* / num [unit])*"
# ---------------------------------------------------------------------------

def _parse_expr(tokens: list) -> Quantity:
    """Parse a sequence of quantity tokens into a single Quantity.

    Grammar (informal):
        expr  = atom (op atom)*
        atom  = NUM UNIT?
        op    = '*' | '/'
    """
    if not tokens:
        return Quantity(0.0, {})

    result = _parse_atom(tokens, 0)
    pos = result[1]
    qty = result[0]

    while pos < len(tokens):
        tok_type, tok_val = tokens[pos]
        if tok_type != "op":
            break
        op = tok_val
        pos += 1
        rhs_qty, pos = _parse_atom(tokens, pos)
        if op == "*":
            qty = multiply(qty, rhs_qty)
        elif op == "/":
            qty = divide(qty, rhs_qty)

    return qty


def _parse_atom(tokens: list, pos: int):
    """Parse one atom (number + optional unit) starting at *pos*.

    Returns (Quantity, new_pos).
    """
    if pos >= len(tokens):
        raise ValueError(f"Expected number at position {pos}")

    tok_type, tok_val = tokens[pos]
    if tok_type != "num":
        raise ValueError(f"Expected number, got {tok_type!r}={tok_val!r} at {pos}")
    magnitude = tok_val
    pos += 1

    # Optional unit
    dims: Dict[str, int] = {}
    if pos < len(tokens) and tokens[pos][0] == "unit":
        unit_sym = tokens[pos][1]
        dims = {unit_sym: 1}
        pos += 1

    return Quantity(magnitude, dims), pos
