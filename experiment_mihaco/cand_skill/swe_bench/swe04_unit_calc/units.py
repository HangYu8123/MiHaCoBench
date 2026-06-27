"""units.py — Quantity value type for the dimensional-unit calculator."""


class Quantity:
    """A physical quantity with a magnitude and a dimension map.

    Attributes:
        magnitude: float — the numeric value.
        _dim: dict — maps base-unit strings (e.g. 'm', 's', 'kg') to
              integer exponents. Keys with exponent 0 are omitted.
    """

    def __init__(self, magnitude: float, dim: dict):
        self.magnitude = float(magnitude)
        # Store a clean copy with zero-exponent keys removed.
        self._dim = {unit: exp for unit, exp in dim.items() if exp != 0}

    def __repr__(self):
        return f"Quantity(magnitude={self.magnitude}, dim={self._dim})"
