"""invoice.py — Invoice facade for line-item billing with per-line tax rounding."""

import tax


def format_cents(cents: int) -> str:
    """Render an integer number of cents as '$X.YY'.

    Examples:
        format_cents(494) == '$4.94'
        format_cents(5)   == '$0.05'
        format_cents(100) == '$1.00'
        format_cents(0)   == '$0.00'
    """
    dollars = cents // 100
    remaining_cents = cents % 100
    return f"${dollars}.{remaining_cents:02d}"


class Invoice:
    def __init__(self) -> None:
        self._lines = []  # list of (desc, unit_price_cents, qty, tax_rate)

    def add_line(self, desc: str, unit_price_cents: int, qty: int,
                 tax_rate: float) -> None:
        """Append a line item."""
        self._lines.append((desc, unit_price_cents, qty, tax_rate))

    def subtotal(self) -> int:
        """Sum of unit_price_cents * qty over all lines (whole cents)."""
        return sum(unit_price_cents * qty for _, unit_price_cents, qty, _ in self._lines)

    def tax_total(self) -> int:
        """Sum over lines of tax.line_tax(unit_price_cents * qty, tax_rate).

        Tax is computed PER LINE (each rounded individually) and THEN summed.
        """
        return sum(
            tax.line_tax(unit_price_cents * qty, tax_rate)
            for _, unit_price_cents, qty, tax_rate in self._lines
        )

    def total(self) -> int:
        """subtotal() + tax_total() (whole cents)."""
        return self.subtotal() + self.tax_total()
