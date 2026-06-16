"""ops.py — arithmetic operations on Quantity objects.

All operations return a *new* Quantity; the inputs are never mutated.

NOTE: This is the BROKEN reference.  The divide() function incorrectly
ADDS the divisor's dimension exponents instead of subtracting them.
Everything else is correct.
"""
from __future__ import annotations

from units import Quantity


def multiply(a: Quantity, b: Quantity) -> Quantity:
    """Return a * b.

    magnitude = a.magnitude * b.magnitude
    dimension = element-wise SUM of both dimension maps (exponents add).
    """
    new_mag = a.magnitude * b.magnitude
    new_dims = dict(a.dim_map())
    for unit, exp in b.dim_map().items():
        new_dims[unit] = new_dims.get(unit, 0) + exp
    # drop zeros
    new_dims = {k: v for k, v in new_dims.items() if v != 0}
    return Quantity(new_mag, new_dims)


def divide(a: Quantity, b: Quantity) -> Quantity:
    """Return a / b.

    BUG: exponents are ADDED instead of subtracted, so 'm / s' gives
    dimension {'m': 1, 's': 1} instead of the correct {'m': 1, 's': -1}.
    Magnitude arithmetic is still correct.
    """
    new_mag = a.magnitude / b.magnitude
    new_dims = dict(a.dim_map())
    for unit, exp in b.dim_map().items():
        new_dims[unit] = new_dims.get(unit, 0) + exp  # BUG: should be -=
    # drop zeros
    new_dims = {k: v for k, v in new_dims.items() if v != 0}
    return Quantity(new_mag, new_dims)


def add(a: Quantity, b: Quantity) -> Quantity:
    """Return a + b.

    Raises ValueError if a and b have incompatible dimensions.

    magnitude = a.magnitude + b.magnitude
    dimension = unchanged (same as a's and b's shared dimension).
    """
    if not a.dims_equal(b):
        raise ValueError(
            f"Cannot add quantities with incompatible dimensions: "
            f"{a.dim_map()} vs {b.dim_map()}"
        )
    return Quantity(a.magnitude + b.magnitude, a.dim_map())
