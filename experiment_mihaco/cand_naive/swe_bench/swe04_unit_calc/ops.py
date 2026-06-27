"""ops.py — Operations that combine Quantity objects."""

from units import Quantity


def multiply(a: Quantity, b: Quantity) -> Quantity:
    """Multiply two quantities.

    Returns a new Quantity with:
      - magnitude = a.magnitude * b.magnitude
      - dimension = element-wise sum of both dimension maps
    """
    new_magnitude = a.magnitude * b.magnitude
    new_dims = dict(a.dimensions)
    for unit, exp in b.dimensions.items():
        new_dims[unit] = new_dims.get(unit, 0) + exp
    # Remove zero exponents
    new_dims = {u: e for u, e in new_dims.items() if e != 0}
    return Quantity(new_magnitude, new_dims)


def divide(a: Quantity, b: Quantity) -> Quantity:
    """Divide quantity a by quantity b.

    Returns a new Quantity with:
      - magnitude = a.magnitude / b.magnitude
      - dimension = element-wise subtraction of b's exponents from a's
        (zero exponents are omitted)
    """
    new_magnitude = a.magnitude / b.magnitude
    new_dims = dict(a.dimensions)
    for unit, exp in b.dimensions.items():
        new_dims[unit] = new_dims.get(unit, 0) - exp
    # Remove zero exponents
    new_dims = {u: e for u, e in new_dims.items() if e != 0}
    return Quantity(new_magnitude, new_dims)


def add(a: Quantity, b: Quantity) -> Quantity:
    """Add two quantities with identical dimensions.

    Returns a new Quantity with:
      - magnitude = a.magnitude + b.magnitude
      - dimension = same as a and b

    Raises:
        ValueError: if a and b have different dimensions.
    """
    if a.dimensions != b.dimensions:
        raise ValueError(
            f"Cannot add quantities with incompatible dimensions: "
            f"{a.dimensions} vs {b.dimensions}"
        )
    new_magnitude = a.magnitude + b.magnitude
    return Quantity(new_magnitude, dict(a.dimensions))
