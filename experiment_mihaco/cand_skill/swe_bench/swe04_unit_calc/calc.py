"""calc.py — Facade providing parse() and to_dim() for the unit calculator."""

import re
from units import Quantity
from ops import multiply, divide


# Supported base units.
_BASE_UNITS = {'m', 's', 'kg'}


def _parse_token(token: str) -> Quantity:
    """Parse a single token like '3 m', '2.5 kg', '1 s', or '5' (no unit).

    Returns a Quantity.
    """
    token = token.strip()
    # Try matching an optional number followed by an optional unit.
    match = re.fullmatch(
        r'([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([a-zA-Z]*)',
        token
    )
    if match is None:
        raise ValueError(f"Cannot parse token: {repr(token)}")
    magnitude = float(match.group(1))
    unit_str = match.group(2).strip()
    if unit_str == '':
        dim = {}
    elif unit_str in _BASE_UNITS:
        dim = {unit_str: 1}
    else:
        raise ValueError(f"Unknown unit: {repr(unit_str)}")
    return Quantity(magnitude, dim)


def parse(text: str) -> Quantity:
    """Parse a dimensional expression and return a Quantity.

    Supported syntax (left-to-right evaluation):
      "3 m"              → magnitude 3.0, dimension {'m': 1}
      "2 m * 3 s"        → magnitude 6.0, dimension {'m': 1, 's': 1}
      "4 m / 2 s"        → magnitude 2.0, dimension {'m': 1, 's': -1}
      "12 m / 2 s / 3 s" → magnitude 2.0, dimension {'m': 1, 's': -2}
      "6 m / 2 m"        → magnitude 3.0, dimension {}
      "5"                → magnitude 5.0, dimension {}
    """
    text = text.strip()

    # Tokenise on operators '*' and '/', keeping the operators as delimiters.
    # Split on '*' or '/' surrounded by optional whitespace.
    parts = re.split(r'\s*([*/])\s*', text)
    # parts alternates: [operand, op, operand, op, operand, ...]

    if not parts:
        raise ValueError(f"Empty expression: {repr(text)}")

    result = _parse_token(parts[0])

    i = 1
    while i < len(parts):
        op = parts[i]
        operand = _parse_token(parts[i + 1])
        if op == '*':
            result = multiply(result, operand)
        elif op == '/':
            result = divide(result, operand)
        else:
            raise ValueError(f"Unknown operator: {repr(op)}")
        i += 2

    return result


def to_dim(q: Quantity) -> dict:
    """Return a copy of the dimension map of q.

    Keys with exponent 0 are omitted. The returned dict maps base-unit
    strings to integer exponents.
    """
    return dict(q._dim)
