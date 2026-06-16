"""tax.py — Per-line tax computation."""

from decimal import Decimal
import money


def line_tax(amount_cents: int, rate: float) -> int:
    """Compute tax for a single line item.

    Parameters
    ----------
    amount_cents : int
        The line item amount in whole cents.
    rate : float
        The tax rate (e.g. 0.0825 for 8.25%).

    Returns
    -------
    int
        The tax amount in whole cents, rounded half-to-even.
    """
    exact = Decimal(str(amount_cents)) * Decimal(str(rate))
    return money.round_cents(exact)
