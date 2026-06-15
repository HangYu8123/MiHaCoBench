# Complex 04 — `formula_engine`: spreadsheet formula evaluator

**Created:** 2026-06-15 · **Category:** complex · **Weight:** 5

Implement a mini spreadsheet engine spread across **four files**:

| File | Responsibility |
|---|---|
| `lexer.py` | Tokenizer: breaks a formula string into tokens |
| `parser.py` | Recursive-descent / Pratt parser that builds an AST |
| `evaluator.py` | Walks the AST and evaluates it against a `Sheet` |
| `sheet.py` | **Facade**: exposes the public `Sheet` class |

Use **numpy** (≥1.26) for range-aggregation functions (SUM, AVG, MIN, MAX).
The standard library is fine for everything else.
Do **not** import any other packages.

---

## Public contract

```python
from sheet import Sheet          # the only import the grader uses

class Sheet:
    def set_cell(self, ref: str, content: str) -> None: ...
    def get_value(self, ref: str) -> float | str: ...
    def recalculate(self) -> None: ...
```

### `set_cell(ref, content)`

* `ref` is a cell address like `"A1"`, `"B2"`, `"Z99"` (one or more uppercase
  letters followed by one or more digits).
* `content` is one of:
  * A bare number (`"3.5"`, `"-1"`, `"0"`) — stored as a float.
  * Arbitrary text (anything that does not start with `=`) — stored as a string.
  * A formula string starting with `=` — stored; evaluated lazily on `get_value`.

### `get_value(ref) -> float | str`

Evaluates and returns the cell's current value:

* Number cells return a `float`.
* Text cells return a `str`.
* Formula cells are evaluated against the current cell values and return
  `float` or `str`.
* If evaluation requires a cell that has not been set, treat it as `0.0`.

### `recalculate() -> None`

Forces all formula cells to be re-evaluated. After `recalculate()` returns,
subsequent `get_value` calls on any cell must reflect the latest values.

---

## Formula language

### Literals and cell references

* Integer and float literals: `2`, `3.14`, `-1.5`
* Cell references: `A1`, `B2`, `AA10` (letters then digits)

### Arithmetic operators (correct precedence, left-associative except `^`)

| Operator | Precedence | Notes |
|---|---|---|
| `+` `-` | lowest (1) | left-associative |
| `*` `/` | medium (2) | left-associative |
| `^` | highest (3) | right-associative (optional — `=2^3` must equal `8.0`) |

Parentheses override precedence: `=(2+3)*4` → `20.0`.

### Range aggregation functions

Ranges are written `A1:B3` (top-left `:` bottom-right). Functions accept a
single range argument OR a comma-separated list of cell references / literals.

| Function | Semantics |
|---|---|
| `SUM(A1:A3)` | sum of the numeric values in the range |
| `AVG(A1:A3)` | arithmetic mean of the numeric values |
| `MIN(A1:A3)` | minimum of the numeric values |
| `MAX(A1:A3)` | maximum of the numeric values |

Non-numeric cells in a range are skipped (treated as 0.0 for SUM/AVG or
ignored for MIN/MAX if there are any numeric cells).

### Conditional function

```
IF(condition, value_if_true, value_if_false)
```

`condition` is an expression using one comparison operator:
`=` (equality), `<>` (not-equal), `<`, `<=`, `>`, `>=`.

Examples:
* `=IF(A1>A2, 10, 20)` → `10.0` when A1 > A2, else `20.0`
* `=IF(A1=A2, "same", "diff")` → `"same"` or `"diff"`

The `value_if_true` and `value_if_false` branches may be numeric expressions,
string literals (double-quoted), or cell references.

### Cycle detection

If setting or evaluating a cell would create a **dependency cycle**
(e.g. `A1 = =A2` and `A2 = =A1`), a **`ValueError`** must be raised.
The exception may be raised either on `set_cell` or on the first `get_value`
that triggers the cycle — both are acceptable.

---

## Example session

```python
s = Sheet()
s.set_cell("A1", "2")
s.set_cell("A2", "3")
s.set_cell("A3", "=A1+A2")
assert s.get_value("A3") == 5.0          # basic formula

s.set_cell("A1", "10")
s.recalculate()
assert s.get_value("A3") == 13.0         # propagation after update

s.set_cell("B1", "=SUM(A1:A2)")
assert s.get_value("B1") == 13.0         # SUM over a range

s.set_cell("C1", "=IF(A1>A2, 1, 0)")
assert s.get_value("C1") == 1.0          # conditional
```

---

## Constraints

* The solution must be split across the four files listed above.
* `sheet.py` must expose exactly the `Sheet` class; the grader does
  `from sheet import Sheet`.
* You may add helper modules if you wish, but the four named files must exist.
