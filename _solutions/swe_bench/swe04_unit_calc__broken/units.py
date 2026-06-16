"""units.py — Quantity value type for the dimensional-unit calculator.

A Quantity bundles a floating-point magnitude with an SI dimension map.
The dimension map is a dict from base-unit symbol to integer exponent, e.g.:
    {'m': 1, 's': -1}   → metres per second
    {'kg': 1, 'm': 1, 's': -2}  → Newtons
Keys with exponent 0 are never stored (they are dropped on creation).
"""
from __future__ import annotations

from typing import Dict


class Quantity:
    """A physical quantity: a magnitude paired with a dimensional unit."""

    def __init__(self, magnitude: float, dimensions: Dict[str, int] | None = None) -> None:
        self.magnitude: float = float(magnitude)
        # Normalize: drop zero-exponent entries
        raw = dimensions or {}
        self._dims: Dict[str, int] = {k: v for k, v in raw.items() if v != 0}

    # ------------------------------------------------------------------
    # Dimension access
    # ------------------------------------------------------------------
    def dim_map(self) -> Dict[str, int]:
        """Return a copy of the dimension map (zero entries excluded)."""
        return dict(self._dims)

    def dims_equal(self, other: "Quantity") -> bool:
        """True iff both quantities share the same dimension map."""
        return self._dims == other._dims

    # ------------------------------------------------------------------
    # Dunder helpers (for readability in tests/REPL)
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return f"Quantity({self.magnitude!r}, {self._dims!r})"

    def __eq__(self, other: object) -> bool:  # pragma: no cover
        if not isinstance(other, Quantity):
            return NotImplemented
        return (
            abs(self.magnitude - other.magnitude) < 1e-9
            and self._dims == other._dims
        )
