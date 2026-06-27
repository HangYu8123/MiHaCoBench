from decimal import Decimal, ROUND_HALF_EVEN


def round_cents(exact) -> int:
    """Round an exact monetary amount in cents to the nearest whole cent.

    Uses half-to-even (banker's) rounding.
    Accepts Decimal, float, or int.
    Float inputs are interpreted by their decimal text value to avoid
    binary float precision issues.
    """
    if isinstance(exact, Decimal):
        d = exact
    else:
        d = Decimal(str(exact))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
