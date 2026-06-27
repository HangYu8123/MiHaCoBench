"""ops.py — arithmetic operations on Quantity objects."""

from units import Quantity


def multiply(a: Quantity, b: Quantity) -> Quantity:
    """Return a new Quantity = a * b.

    magnitude = a.magnitude * b.magnitude
    dimension = element-wise sum of both dimension maps (exponents add).
    """
    new_dims = dict(a._dims)
    for unit, exp in b._dims.items():
        new_dims[unit] = new_dims.get(unit, 0) + exp
    # Prune zero-exponent keys (unit cancellation).
    new_dims = {u: e for u, e in new_dims.items() if e != 0}
    return Quantity(a.magnitude * b.magnitude, new_dims)


def divide(a: Quantity, b: Quantity) -> Quantity:
    """Return a new Quantity = a / b.

    magnitude = a.magnitude / b.magnitude
    dimension = element-wise subtraction of b's exponents from a's.
    Zero-exponent entries are omitted (unit cancellation).
    """
    new_dims = dict(a._dims)
    for unit, exp in b._dims.items():
        new_dims[unit] = new_dims.get(unit, 0) - exp  # subtract, not add
    # Prune zero-exponent keys (unit cancellation).
    new_dims = {u: e for u, e in new_dims.items() if e != 0}
    return Quantity(a.magnitude / b.magnitude, new_dims)


def add(a: Quantity, b: Quantity) -> Quantity:
    """Return a new Quantity = a + b.

    Raises ValueError if a and b have different dimensions.
    """
    if a._dims != b._dims:
        raise ValueError(
            f"Incompatible dimensions: {a._dims} vs {b._dims}"
        )
    return Quantity(a.magnitude + b.magnitude, dict(a._dims))
