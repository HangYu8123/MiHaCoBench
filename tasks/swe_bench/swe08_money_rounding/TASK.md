# SWE-Bench 08 — `money_rounding`: Invoice Totals with Per-Line Tax Rounding

**Created:** 2026-06-16 · **Category:** swe_bench · **Weight:** 6

A small invoicing engine totals line items in whole cents.  The bug is observed
at the **facade** (`invoice.py`): `Invoice.total()` / `Invoice.tax_total()` come
back one cent *low* on certain lines.  The **root cause** is not in `invoice.py`
or `tax.py` — it lives one module deeper, in the rounding helper in `money.py`.

This is a SWE-bench-style multi-file fault-localisation task: the symptom and the
defect are in different files, and you must trace across the module boundary to
fix the right one.

---

## Files to create

```
money.py     — round_cents(exact) -> int          (this file holds the bug)
tax.py       — line_tax(amount_cents, rate) -> int (calls money.round_cents)
invoice.py   — FACADE: class Invoice + format_cents (the symptom surfaces here)
```

Use **stdlib only** — no third-party packages.  Use the `decimal` module for
exact monetary arithmetic.

---

## Public contract

### `money.py`

| Name | Signature | Behaviour |
|---|---|---|
| `round_cents(exact)` | `round_cents(exact: decimal.Decimal \| float \| int) -> int` | Round an exact monetary amount expressed **in cents** to the nearest whole cent, with ties resolved **half-to-even** (banker's rounding). Returns a plain `int`. |

`round_cents` must use proper round-half-to-even — e.g. via
`decimal.Decimal(...).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)` — and
return `int`.  It must NOT truncate.  Documented tie behaviour (exact values):

```
round_cents(Decimal("0.5")) == 0     round_cents(Decimal("1.5")) == 2
round_cents(Decimal("2.5")) == 2     round_cents(Decimal("3.5")) == 4
round_cents(Decimal("493.7625")) == 494   # fractional part > 0.5 rounds up
```

Floats passed to `round_cents` are interpreted by their decimal text value
(i.e. `0.0825` means exactly 825/10000), not their binary expansion.

### `tax.py`

| Name | Signature | Behaviour |
|---|---|---|
| `line_tax(amount_cents, rate)` | `line_tax(amount_cents: int, rate: float) -> int` | Compute `amount_cents * rate` as an **exact** `Decimal` and return `money.round_cents(...)` of it. |

Worked example: `line_tax(17955, 0.0825)` → `17955 * 0.0825 = 1481.2875` cents
→ `1481`.  And `line_tax(5985, 0.0825)` → `493.7625` → `494`.

### `invoice.py` (facade)

```python
from invoice import Invoice          # must work exactly like this

class Invoice:
    def __init__(self) -> None: ...

    def add_line(self, desc: str, unit_price_cents: int, qty: int,
                 tax_rate: float) -> None:
        """Append a line item."""

    def subtotal(self) -> int:
        """Sum of unit_price_cents * qty over all lines (whole cents)."""

    def tax_total(self) -> int:
        """Sum over lines of tax.line_tax(unit_price_cents * qty, tax_rate).
        Tax is computed PER LINE (each rounded individually) and THEN summed."""

    def total(self) -> int:
        """subtotal() + tax_total() (whole cents)."""
```

`invoice.py` must also provide a render helper:

| Name | Signature | Behaviour |
|---|---|---|
| `format_cents(cents)` | `format_cents(cents: int) -> str` | Render an integer number of cents as `"$X.YY"`. e.g. `format_cents(494) == "$4.94"`, `format_cents(5) == "$0.05"`, `format_cents(100) == "$1.00"`, `format_cents(0) == "$0.00"`. |

All money quantities (`subtotal`, `tax_total`, `total`) are **`int` cents**.

Worked invoice example:

```
inv = Invoice()
inv.add_line("widget", unit_price_cents=1995, qty=3, tax_rate=0.0825)
# line amount = 1995 * 3 = 5985 cents
# exact tax   = 5985 * 0.0825 = 493.7625 cents -> round -> 494
inv.subtotal()  == 5985
inv.tax_total() == 494
inv.total()     == 6479
```

---

## Known bug description (for SWE-bench fault localisation)

**Symptom (in `invoice.py`):** for lines whose exact per-line tax has a
fractional-cent part greater than half a cent, `Invoice.tax_total()` and
`Invoice.total()` come back exactly one cent short.

**Root cause (in `money.py`):** `round_cents` *truncates* the exact amount
toward zero (e.g. via `int(exact)`) instead of rounding half-to-even.  So
`493.7625 -> 493` (should be `494`) and `3.5 -> 3` (should be `4`).  Lines whose
exact tax is already a whole number of cents — and the tie value `2.5` (which is
even-down to `2`, the same as truncation) — are unaffected, which is why the bug
hides on many inputs.

**Your task:** fix `round_cents` in `money.py` so it rounds half-to-even.  Do
not change the per-line tax-then-sum order in `invoice.py`, and do not change
`tax.py`.

---

## Constraints

- **Stdlib only** — no third-party packages.  Use `decimal` for exactness.
- All monetary amounts are whole-cent `int`s.
- `from invoice import Invoice` must succeed.
- The grader imports `Invoice` and `format_cents` from `invoice.py`, `line_tax`
  from `tax.py`, and `round_cents` from `money.py`, and asserts exact
  integer-cent equality.
