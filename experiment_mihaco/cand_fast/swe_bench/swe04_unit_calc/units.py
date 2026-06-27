"""units.py — Quantity value type for the dimensional-unit calculator."""


class Quantity:
    """A physical quantity with a magnitude and a dimension map.

    Args:
        magnitude: numeric value (float).
        dims: dict mapping base-unit strings to integer exponents,
              e.g. {'m': 1, 's': -1}.  Defaults to {} (dimensionless).
    """

    def __init__(self, magnitude: float, dims: dict = None):
        self.magnitude = float(magnitude)
        # Store a private copy so callers cannot mutate our internals.
        self._dims = dict(dims) if dims is not None else {}

    def __repr__(self):
        return f"Quantity({self.magnitude}, {self._dims})"
