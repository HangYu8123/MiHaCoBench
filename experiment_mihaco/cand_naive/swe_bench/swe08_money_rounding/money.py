"""money.py — monetary rounding helper."""

import decimal
from decimal import Decimal, ROUND_HALF_EVEN


def round_cents(exact) -> int:
    """Round an exact monetary amount in cents to the nearest whole cent.

    Ties are resolved half-to-even (banker's rounding).
    Returns a plain int.

    Floats are interpreted by their decimal text value, not binary expansion.
    """
    if isinstance(exact, float):
        d = Decimal(str(exact))
    else:
        d = Decimal(exact)
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
