"""tax.py — per-line tax calculation."""

from decimal import Decimal
import money


def line_tax(amount_cents: int, rate: float) -> int:
    """Compute amount_cents * rate as an exact Decimal and return rounded cents.

    Uses money.round_cents for half-to-even rounding.
    """
    exact = Decimal(amount_cents) * Decimal(str(rate))
    return money.round_cents(exact)
