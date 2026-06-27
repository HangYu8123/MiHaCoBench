"""invoice.py — Invoice facade.

Provides the Invoice class and format_cents helper.
"""

import tax


def format_cents(cents: int) -> str:
    """Render an integer number of cents as '$X.YY'.

    Args:
        cents: A non-negative integer number of cents.

    Returns:
        Formatted string like '$4.94', '$0.05', '$1.00', '$0.00'.

    Examples:
        format_cents(494)  == '$4.94'
        format_cents(5)    == '$0.05'
        format_cents(100)  == '$1.00'
        format_cents(0)    == '$0.00'
    """
    dollars = cents // 100
    remaining_cents = cents % 100
    return f"${dollars}.{remaining_cents:02d}"


class Invoice:
    """Simple invoicing engine that totals line items in whole cents."""

    def __init__(self) -> None:
        self._lines: list[dict] = []

    def add_line(self, desc: str, unit_price_cents: int, qty: int,
                 tax_rate: float) -> None:
        """Append a line item.

        Args:
            desc: Description of the line item.
            unit_price_cents: Price per unit in whole cents.
            qty: Quantity of units.
            tax_rate: Tax rate as a float (e.g. 0.0825 for 8.25%).
        """
        self._lines.append({
            "desc": desc,
            "unit_price_cents": unit_price_cents,
            "qty": qty,
            "tax_rate": tax_rate,
        })

    def subtotal(self) -> int:
        """Sum of unit_price_cents * qty over all lines (whole cents).

        Returns:
            Total pre-tax amount in whole cents as an int.
        """
        return sum(line["unit_price_cents"] * line["qty"]
                   for line in self._lines)

    def tax_total(self) -> int:
        """Sum of per-line tax, each rounded individually then summed.

        Tax is computed PER LINE (each rounded individually) and THEN summed.

        Returns:
            Total tax amount in whole cents as an int.
        """
        return sum(
            tax.line_tax(line["unit_price_cents"] * line["qty"],
                         line["tax_rate"])
            for line in self._lines
        )

    def total(self) -> int:
        """subtotal() + tax_total() in whole cents.

        Returns:
            Total invoice amount (pre-tax + tax) in whole cents as an int.
        """
        return self.subtotal() + self.tax_total()
