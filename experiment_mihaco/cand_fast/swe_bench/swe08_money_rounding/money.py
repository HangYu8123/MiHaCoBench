from decimal import Decimal, ROUND_HALF_EVEN


def round_cents(exact) -> int:
    """Round an exact monetary amount in cents to the nearest whole cent,
    with ties resolved half-to-even (banker's rounding). Returns a plain int."""
    if isinstance(exact, float):
        d = Decimal(str(exact))
    elif isinstance(exact, int):
        d = Decimal(exact)
    else:
        # Assume Decimal or Decimal-compatible
        d = Decimal(str(exact)) if not isinstance(exact, Decimal) else exact
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
