"""calc.py — Facade: parse(text) -> Quantity and to_dim(q) -> dict."""

import re
from units import Quantity
from ops import multiply, divide

# Base units recognised by the parser
BASE_UNITS = {'m', 's', 'kg'}


def _parse_term(text: str) -> Quantity:
    """Parse a single term like '3 m', '2.5 kg', '1 s', or '5' (no unit)."""
    text = text.strip()
    # Try to match optional number followed by optional unit
    match = re.fullmatch(
        r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*([a-zA-Z]*)', text
    )
    if match is None:
        raise ValueError(f"Cannot parse term: {repr(text)}")
    magnitude_str, unit_str = match.group(1), match.group(2).strip()
    magnitude = float(magnitude_str)
    if unit_str == '':
        # Pure number, dimensionless
        dims = {}
    elif unit_str in BASE_UNITS:
        dims = {unit_str: 1}
    else:
        raise ValueError(f"Unknown unit: {repr(unit_str)}")
    return Quantity(magnitude, dims)


def parse(text: str) -> Quantity:
    """Parse a dimensional expression and return a Quantity.

    Supported forms:
        "3 m"              single quantity
        "2 m * 3 s"        multiplication
        "4 m / 2 s"        division
        "12 m / 2 s / 3 s" chained division
        "6 m / 2 m"        unit cancellation → dimension {}
        "5"                pure number → dimension {}

    Operators are evaluated left-to-right.
    """
    text = text.strip()
    # Tokenise: split on '*' or '/' while keeping the operator
    token_pattern = re.compile(r'(\*|/)')
    parts = token_pattern.split(text)
    # parts alternates: term, op, term, op, term, ...
    # First element is always a term
    result = _parse_term(parts[0])
    i = 1
    while i < len(parts):
        op = parts[i].strip()
        operand = _parse_term(parts[i + 1])
        if op == '*':
            result = multiply(result, operand)
        elif op == '/':
            result = divide(result, operand)
        else:
            raise ValueError(f"Unknown operator: {repr(op)}")
        i += 2
    return result


def to_dim(q: Quantity) -> dict:
    """Return a copy of the dimension map of q (zero exponents omitted)."""
    return q.dimensions
