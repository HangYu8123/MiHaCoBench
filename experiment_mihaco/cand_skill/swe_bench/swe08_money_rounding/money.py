"""money.py — monetary rounding helper.

Provides round_cents() with half-to-even (banker's) rounding.
"""

from decimal import Decimal, ROUND_HALF_EVEN


def round_cents(exact) -> int:
    """Round an exact monetary amount in cents to the nearest whole cent.

    Ties are resolved half-to-even (banker's rounding).

    Args:
        exact: The exact amount in cents as a Decimal, float, or int.
               Floats are interpreted by their decimal text value
               (e.g. 0.0825 means exactly 825/10000).

    Returns:
        Nearest whole cent as a plain int.
    """
    # Convert via str() to capture the decimal text value, not the binary
    # float approximation. str(Decimal) and str(int) are also safe.
    d = Decimal(str(exact))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
