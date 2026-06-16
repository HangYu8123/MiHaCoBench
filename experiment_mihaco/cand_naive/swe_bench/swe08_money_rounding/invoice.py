"""invoice.py — Invoice facade for line-item billing with per-line tax rounding."""

import tax


def format_cents(cents: int) -> str:
    """Render an integer number of cents as a dollar string.

    Parameters
    ----------
    cents : int
        Amount in whole cents.

    Returns
    -------
    str
        Formatted as "$X.YY", e.g. format_cents(494) == "$4.94".
    """
    dollars, remaining_cents = divmod(abs(cents), 100)
    sign = "-" if cents < 0 else ""
    return f"{sign}${dollars}.{remaining_cents:02d}"


class Invoice:
    """Simple invoice that accumulates line items and computes totals."""

    def __init__(self) -> None:
        self._lines = []  # list of (desc, unit_price_cents, qty, tax_rate)

    def add_line(self, desc: str, unit_price_cents: int, qty: int,
                 tax_rate: float) -> None:
        """Append a line item."""
        self._lines.append((desc, unit_price_cents, qty, tax_rate))

    def subtotal(self) -> int:
        """Sum of unit_price_cents * qty over all lines (whole cents)."""
        return sum(unit_price * qty for _, unit_price, qty, _ in self._lines)

    def tax_total(self) -> int:
        """Sum over lines of tax.line_tax(unit_price_cents * qty, tax_rate).

        Tax is computed PER LINE (each rounded individually) and THEN summed.
        """
        return sum(
            tax.line_tax(unit_price * qty, rate)
            for _, unit_price, qty, rate in self._lines
        )

    def total(self) -> int:
        """subtotal() + tax_total() (whole cents)."""
        return self.subtotal() + self.tax_total()
