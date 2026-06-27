"""ops.py — Operations on Quantity objects: multiply, divide, add."""

from units import Quantity


def multiply(a: Quantity, b: Quantity) -> Quantity:
    """Return a new Quantity whose magnitude is a*b and whose dimension is
    the element-wise sum of both dimension maps (exponents add).
    """
    magnitude = a.magnitude * b.magnitude
    all_units = a._dim.keys() | b._dim.keys()
    dim = {
        u: a._dim.get(u, 0) + b._dim.get(u, 0)
        for u in all_units
        if a._dim.get(u, 0) + b._dim.get(u, 0) != 0
    }
    return Quantity(magnitude, dim)


def divide(a: Quantity, b: Quantity) -> Quantity:
    """Return a new Quantity whose magnitude is a/b and whose dimension is
    the element-wise subtraction of b's exponents from a's.

    Units that cancel (result exponent == 0) are omitted from the dimension map.
    """
    magnitude = a.magnitude / b.magnitude
    all_units = a._dim.keys() | b._dim.keys()
    dim = {
        u: a._dim.get(u, 0) - b._dim.get(u, 0)
        for u in all_units
        if a._dim.get(u, 0) - b._dim.get(u, 0) != 0
    }
    return Quantity(magnitude, dim)


def add(a: Quantity, b: Quantity) -> Quantity:
    """Return a new Quantity whose magnitude is a+b with the same dimension.

    Raises ValueError if a and b have different dimensions (incompatible units).
    """
    if a._dim != b._dim:
        raise ValueError(
            f"Cannot add quantities with different dimensions: "
            f"{a._dim} vs {b._dim}"
        )
    return Quantity(a.magnitude + b.magnitude, dict(a._dim))
