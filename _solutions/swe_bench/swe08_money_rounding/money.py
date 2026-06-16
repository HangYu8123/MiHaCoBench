"""money.py — exact monetary rounding helpers for the invoice engine.

This module is the single source of truth for converting an *exact* monetary
amount (expressed in cents) into a whole number of cents.  Currency must never
be represented with binary floating point at the rounding boundary, so this
module uses :mod:`decimal` and banker's rounding (ties-to-even).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
from typing import Union

Number = Union[Decimal, float, int]


def round_cents(exact: Number) -> int:
    """Round an exact monetary amount in cents to the nearest whole cent.

    Ties are resolved half-to-even (banker's rounding), e.g. ``2.5 -> 2`` and
    ``3.5 -> 4``.  ``exact`` may be a :class:`~decimal.Decimal`, ``float`` or
    ``int``.  Floats are converted through ``str`` so the human-readable decimal
    value (not its binary expansion) is what gets rounded.

    Returns a plain ``int`` number of cents.
    """
    if isinstance(exact, Decimal):
        d = exact
    else:
        d = Decimal(str(exact))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
