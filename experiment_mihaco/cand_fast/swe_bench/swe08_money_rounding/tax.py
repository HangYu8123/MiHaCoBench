from decimal import Decimal
import money


def line_tax(amount_cents: int, rate: float) -> int:
    """Compute amount_cents * rate as an exact Decimal and return rounded cents.

    Uses Decimal arithmetic to avoid binary float precision issues.
    The rate float is converted via str() to capture its decimal text value.
    """
    exact = Decimal(amount_cents) * Decimal(str(rate))
    return money.round_cents(exact)
