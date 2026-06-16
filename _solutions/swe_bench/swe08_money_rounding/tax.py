"""tax.py — per-line tax computation for the invoice engine.

The tax for a single line is the line's amount (in cents) multiplied by its tax
rate, rounded to a whole number of cents.  The multiplication is performed with
:class:`~decimal.Decimal` so the exact fractional-cent value is preserved up to
the moment it is rounded by :func:`money.round_cents`.
"""
from __future__ import annotations

from decimal import Decimal

import money


def line_tax(amount_cents: int, rate: float) -> int:
    """Return the tax in whole cents for ``amount_cents`` at ``rate``.

    ``amount_cents * rate`` is computed exactly as a :class:`~decimal.Decimal`
    (the rate is taken through ``str`` so e.g. ``0.0825`` means exactly that),
    then handed to :func:`money.round_cents`.

    Example: ``line_tax(17955, 0.0825)`` -> ``17955 * 0.0825 = 1481.2875`` cents
    -> ``1481``.
    """
    exact = Decimal(int(amount_cents)) * Decimal(str(rate))
    return money.round_cents(exact)
