"""calc.py — Facade re-exporting parse() and to_dim()."""

from units import Quantity
from ops import multiply, divide


def parse(text: str) -> Quantity:
    """Parse a dimensional expression and return a Quantity.

    Supported syntax (whitespace around operators is flexible):
        "3 m"           -> Quantity(3.0, {'m': 1})
        "2 m * 3 s"     -> Quantity(6.0, {'m': 1, 's': 1})
        "4 m / 2 s"     -> Quantity(2.0, {'m': 1, 's': -1})
        "12 m / 2 s / 3 s" -> Quantity(2.0, {'m': 1, 's': -2})
        "6 m / 2 m"     -> Quantity(3.0, {})
        "5"             -> Quantity(5.0, {})
    """
    tokens = text.split()

    # Build a list of (operator, Quantity) pairs.
    # We scan tokens left-to-right:
    #   number [unit] [op number [unit] ...]
    # where op is '*' or '/'.

    result = None
    pending_op = None  # '*' or '/' — operator before the next quantity
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        if tok in ('*', '/'):
            pending_op = tok
            i += 1
            continue

        # tok should be a number
        try:
            magnitude = float(tok)
        except ValueError:
            raise ValueError(f"Unexpected token: {tok!r}")

        i += 1

        # Check if the next token is a unit (not an operator and not a number)
        dims = {}
        if i < len(tokens) and tokens[i] not in ('*', '/'):
            try:
                float(tokens[i])
                # It's a plain number — no unit for this quantity
            except ValueError:
                # It's a unit string
                dims = {tokens[i]: 1}
                i += 1

        q = Quantity(magnitude, dims)

        if result is None:
            result = q
        elif pending_op == '*':
            result = multiply(result, q)
            pending_op = None
        elif pending_op == '/':
            result = divide(result, q)
            pending_op = None
        else:
            raise ValueError(f"Missing operator between quantities")

    if result is None:
        raise ValueError("Empty expression")

    return result


def to_dim(q: Quantity) -> dict:
    """Return a copy of q's dimension map.

    Keys with exponent 0 are omitted. The returned dict is a fresh copy
    so external mutation does not corrupt the Quantity's internal state.
    """
    return {u: e for u, e in q._dims.items() if e != 0}
