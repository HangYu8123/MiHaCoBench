"""invoice.py — FACADE for the invoice engine.

Public entry point: ``from invoice import Invoice``.  An :class:`Invoice`
accumulates line items and reports its subtotal, per-line tax total, and grand
total — all as whole numbers of cents (``int``).  Tax is computed *per line*
(rounded individually) and then summed, which is the legally correct order for
most jurisdictions and the reason a rounding bug in :mod:`money` surfaces here.
"""
from __future__ import annotations

from typing import List, Tuple

import tax


def format_cents(cents: int) -> str:
    """Render an integer number of cents as a ``"$X.YY"`` string.

    Example: ``format_cents(494) -> "$4.94"``, ``format_cents(5) -> "$0.05"``.
    """
    cents = int(cents)
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


class Invoice:
    """An invoice that accumulates line items and totals them in whole cents."""

    def __init__(self) -> None:
        # Each line: (description, unit_price_cents, qty, tax_rate)
        self._lines: List[Tuple[str, int, int, float]] = []

    def add_line(self, desc: str, unit_price_cents: int, qty: int,
                 tax_rate: float) -> None:
        """Append a line item.  ``unit_price_cents`` and ``qty`` are ints."""
        self._lines.append((desc, int(unit_price_cents), int(qty), float(tax_rate)))

    def subtotal(self) -> int:
        """Sum of ``unit_price_cents * qty`` over all lines (whole cents)."""
        return sum(unit * qty for _desc, unit, qty, _rate in self._lines)

    def tax_total(self) -> int:
        """Sum of per-line tax (each rounded individually) over all lines."""
        return sum(tax.line_tax(unit * qty, rate)
                   for _desc, unit, qty, rate in self._lines)

    def total(self) -> int:
        """Grand total in whole cents: ``subtotal() + tax_total()``."""
        return self.subtotal() + self.tax_total()
