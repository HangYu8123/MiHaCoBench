# Complex 06 — `spreadsheet_engine`: Mini Spreadsheet Engine

**Created:** 2026-06-15 · **Category:** complex · **Weight:** 5

Implement a mini spreadsheet engine spread across **two files** plus a facade:

| File | Responsibility |
|---|---|
| `dag.py` | Dependency graph using **networkx**: tracks which cells depend on which; provides topological ordering and cycle detection |
| `evaluator.py` | Formula parser and expression evaluator (supports `+`, `-`, `*`, `/` with correct precedence, numeric literals, and cell references like `A1`, `B2`) |
| `sheet.py` | **Facade**: exposes the public `Sheet` class |

Use **networkx** for the dependency DAG and topological ordering.
The standard library is fine for everything else.
Do **not** import any other packages.

---

## Files to create

```
dag.py          — DependencyGraph class wrapping networkx
evaluator.py    — formula tokenizer + evaluator
sheet.py        — Sheet facade (the only file the grader imports from)
```

---

## Public contract

```python
from sheet import Sheet   # the only import the grader uses

class Sheet:
    def set_value(self, cell: str, number: float) -> None: ...
    def set_formula(self, cell: str, expr: str) -> None: ...
    def get_value(self, cell: str) -> float: ...
    def recalc(self) -> None: ...
    def cells_in_topological_order(self) -> list[str]: ...
    def detect_cycle(self) -> bool: ...
```

### `set_value(cell, number)`

* `cell` is a cell address like `"A1"`, `"B2"`, `"Z99"` (one or more uppercase
  letters followed by one or more digits).
* `number` is a `float` (or int coercible to float). Stores the literal value.
* Clears any formula previously stored in the cell.

### `set_formula(cell, expr)`

* `cell` is a cell address (same format as above).
* `expr` is a formula string starting with `=`, e.g. `"=A1+B2*2"`.
* The formula may contain:
  * Cell references: `A1`, `B2`, `AA10` (uppercase letters then digits)
  * Numeric literals: integers or floats (`2`, `3.14`, `0.5`)
  * Arithmetic operators: `+`, `-`, `*`, `/`
  * Parentheses for grouping: `=(A1+B2)*3`
* Operator precedence: `*` and `/` bind tighter than `+` and `-`.
* Stores the formula; does NOT immediately evaluate it.
* Updates the dependency graph: this cell depends on every cell referenced in `expr`.

### `get_value(cell) -> float`

* Returns the current value of the cell as a `float`.
* For literal cells: returns the stored number (or `0.0` if never set).
* For formula cells: evaluates the formula using the current values of all referenced
  cells. References to unset cells are treated as `0.0`.
* If the cell's dependency graph contains a **cycle**, raises **`ValueError`**.

### `recalc() -> None`

* Forces re-evaluation of **all** formula cells in topological order.
* After `recalc()` returns, subsequent `get_value` calls must reflect the latest values.
* If any cycle exists in the dependency graph, raises **`ValueError`**.

### `cells_in_topological_order() -> list[str]`

* Returns the list of all cells that have been set (via `set_value` or `set_formula`)
  in a valid topological order (dependencies before dependents).
* Cells with no dependencies come first.
* If a cycle exists, raises **`ValueError`**.

### `detect_cycle() -> bool`

* Returns `True` if the current dependency graph contains a cycle, `False` otherwise.
* Does **not** raise; safe to call even when cycles exist.

---

## Operator precedence

| Operator | Precedence | Notes |
|---|---|---|
| `+` `-` | lower | left-associative |
| `*` `/` | higher | left-associative |

Parentheses override precedence: `=(2+3)*4` → `20.0`.

---

## Example session

```python
s = Sheet()
s.set_value("A1", 2.0)
s.set_value("B1", 3.0)

# Single formula
s.set_formula("C1", "=A1+B1")
assert s.get_value("C1") == 5.0

# Chained formula: C1 depends on A1 and B1; D1 depends on C1
s.set_formula("D1", "=C1*2")
assert s.get_value("D1") == 10.0

# Update upstream, recalc propagates
s.set_value("A1", 10.0)
s.recalc()
assert s.get_value("C1") == 13.0   # 10 + 3
assert s.get_value("D1") == 26.0   # 13 * 2

# Topological order: A1 and B1 before C1, C1 before D1
order = s.cells_in_topological_order()
assert order.index("A1") < order.index("C1")
assert order.index("C1") < order.index("D1")

# Cycle detection (does not raise)
s2 = Sheet()
s2.set_formula("X1", "=Y1+1")
s2.set_formula("Y1", "=X1+1")
assert s2.detect_cycle() == True

# get_value on a cyclic cell raises ValueError
import pytest
with pytest.raises(ValueError):
    s2.get_value("X1")
```

---

## Constraints

* The solution must be split across the three files listed above.
* `sheet.py` must expose exactly the `Sheet` class; the grader does
  `from sheet import Sheet`.
* `dag.py` must use **networkx** for the dependency graph and topological sort.
* You may add helper functions but the three named files must exist and `sheet.py`
  must be the sole public interface.
