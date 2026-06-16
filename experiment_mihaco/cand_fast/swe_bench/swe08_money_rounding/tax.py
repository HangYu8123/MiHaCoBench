from decimal import Decimal
from money import round_cents


def line_tax(amount_cents: int, rate: float) -> int:
    """Compute amount_cents * rate as an exact Decimal and return
    money.round_cents(...) of it."""
    exact = Decimal(amount_cents) * Decimal(str(rate))
    return round_cents(exact)
