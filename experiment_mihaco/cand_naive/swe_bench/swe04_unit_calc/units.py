"""units.py — Quantity value type for dimensional-unit calculator."""


class Quantity:
    """A physical quantity with a magnitude and a dimensional unit map."""

    def __init__(self, magnitude: float, dimensions: dict = None):
        """
        Args:
            magnitude: The numeric value.
            dimensions: A dict mapping base-unit strings to integer exponents,
                        e.g. {'m': 1, 's': -1}. Zero exponents are omitted.
        """
        self.magnitude = float(magnitude)
        # Store a clean copy with zero exponents removed
        self._dimensions = {
            unit: exp
            for unit, exp in (dimensions or {}).items()
            if exp != 0
        }

    @property
    def dimensions(self) -> dict:
        """Return a copy of the dimension map (zero exponents excluded)."""
        return dict(self._dimensions)
