"""money.py — Monetary rounding helper."""

import decimal
from decimal import Decimal, ROUND_HALF_EVEN


def round_cents(exact) -> int:
    """Round an exact monetary amount (in cents) to the nearest whole cent.

    Uses half-to-even (banker's) rounding.

    Parameters
    ----------
    exact : Decimal | float | int
        The exact amount in cents.

    Returns
    -------
    int
        The rounded whole-cent value.
    """
    if not isinstance(exact, Decimal):
        # Convert via string to avoid float binary-expansion issues
        exact = Decimal(str(exact))
    rounded = exact.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    return int(rounded)
