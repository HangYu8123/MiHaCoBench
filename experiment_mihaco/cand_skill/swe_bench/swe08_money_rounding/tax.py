"""tax.py — per-line tax computation.

Computes exact Decimal tax and delegates rounding to money.round_cents.
"""

from decimal import Decimal

import money


def line_tax(amount_cents: int, rate: float) -> int:
    """Compute tax for a single line item.

    Args:
        amount_cents: The line subtotal in whole cents (int).
        rate: The tax rate as a float (e.g. 0.0825 for 8.25%).
              Interpreted by its decimal text value, not binary expansion.

    Returns:
        The rounded tax amount in whole cents (int).
    """
    # Use str(rate) to get the exact decimal text value (e.g. '0.0825')
    # rather than the binary float approximation.
    exact = Decimal(amount_cents) * Decimal(str(rate))
    return money.round_cents(exact)
