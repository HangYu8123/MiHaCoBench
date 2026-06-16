# SWE-bench 04 — `unit_calc`: dimensional-unit calculator

**Created:** 2026-06-15 · **Category:** swe_bench · **Weight:** 6

Implement a dimensional-unit calculator spread across **three files**:

| File | Responsibility |
|---|---|
| `units.py` | `Quantity` value type: `magnitude: float` + a dimension map `{'m': 1, 's': -1}` |
| `ops.py` | `multiply`, `divide`, `add` operations that combine `Quantity` objects |
| `calc.py` | **Facade** re-exporting `parse(text) -> Quantity` and `to_dim(q) -> dict` |

Base units: metres (`m`), seconds (`s`), kilograms (`kg`).

---

## Public contract

```python
from calc import parse, to_dim

# parse a dimensional expression → Quantity
q = parse("3 m / 2 s")   # Quantity with magnitude 1.5, dimension {'m': 1, 's': -1}

# inspect the dimension map
to_dim(q) -> dict          # e.g. {'m': 1, 's': -1}
```

### `parse(text: str) -> Quantity`

Accepts a text expression and returns a `Quantity` object with:
* `magnitude: float` — the numeric result of the arithmetic.
* an internal dimension map tracking the compound SI unit.

Supported syntax:
* A single quantity: `"3 m"`, `"2.5 kg"`, `"1 s"`
* Multiplication: `"2 m * 3 s"` → magnitude 6, dimension `{'m': 1, 's': 1}`
* Division: `"4 m / 2 s"` → magnitude 2.0, dimension `{'m': 1, 's': -1}`
* Chained: `"12 m / 2 s / 3 s"` → magnitude 2.0, dimension `{'m': 1, 's': -2}`
* Dimensionless (unit cancellation): `"6 m / 2 m"` → magnitude 3.0, dimension `{}`
* Pure number (no unit): `"5"` → magnitude 5.0, dimension `{}`

White space around operators is flexible.

### `to_dim(q: Quantity) -> dict`

Returns a **copy** of the dimension map of `q`. Keys with exponent `0` may be
omitted. The returned dict maps base-unit strings to integer exponents.

### `Quantity` type (from `units.py`)

```python
class Quantity:
    magnitude: float
    # internal dimension map — exact attribute name is not tested,
    # but to_dim(q) must return the correct exponents
```

### `multiply(a: Quantity, b: Quantity) -> Quantity`  (from `ops.py`)

Returns a new `Quantity` whose:
* magnitude = `a.magnitude * b.magnitude`
* dimension = element-wise sum of both dimension maps (exponents add)

### `divide(a: Quantity, b: Quantity) -> Quantity`  (from `ops.py`)

Returns a new `Quantity` whose:
* magnitude = `a.magnitude / b.magnitude`
* dimension = element-wise **subtraction** of `b`'s exponents from `a`'s
  (i.e. if `a` has `s^1` and `b` has `s^1`, the result has `s^0` → omit it)

### `add(a: Quantity, b: Quantity) -> Quantity`  (from `ops.py`)

Returns a new `Quantity` whose:
* magnitude = `a.magnitude + b.magnitude`
* dimension = same as `a` and `b` (they must be identical)
* Raises `ValueError` if `a` and `b` have different dimensions (incompatible units).

---

## Symptom (known defect in the broken reference)

When you **divide** two quantities, the result has **the wrong compound unit**:
instead of subtracting the divisor's dimension exponents, they are added — so
`parse("1 m / 1 s")` reports dimension `{'m': 1, 's': 1}` instead of
`{'m': 1, 's': -1}`. Magnitude arithmetic remains correct.

This makes every compound derived unit (m/s, m/s², etc.) incorrect.

---

## Notes

* Keep the logic in the three named files (`units.py`, `ops.py`, `calc.py`).
* Standard library only — no third-party packages required.
* Assert exceptions by **type** (`ValueError`), not by message text.
* Determinism: identical input → identical output.
