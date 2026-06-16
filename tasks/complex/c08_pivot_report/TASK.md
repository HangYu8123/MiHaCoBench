# Complex 08 — `pivot_report`: Pandas Pivot / Report Engine

**Created:** 2026-06-16 · **Category:** complex · **Weight:** 5

Build a small reporting engine on top of **pandas** (with **numpy**). The work is
split across two files. The grader loads modules by path and imports only from the
facade `report.py` — it does not care about internal structure, only the public
contract below.

This is a spec-density task: the contract pins down exactly how missing
combinations are filled, what the cell dtypes must be, what the margin labels are,
and how ties are broken. Read every sentence — the traps are in the details.

## Files to create

```
frame.py    — build/validate the DataFrame
report.py   — FACADE: class Report (imports build_frame from frame.py)
```

`report.py` must allow:

```python
from report import Report
```

---

## Public contract

### `frame.py` — `build_frame(records: list[dict]) -> pandas.DataFrame`

- Construct a `pandas.DataFrame` from a list of row dicts (one dict per row).
- If `records` is empty (`[]`), raise `ValueError`.

### `report.py` — `class Report(records: list[dict])`

The constructor builds the internal frame via `frame.build_frame(records)`
(so an empty `records` list raises `ValueError` at construction time).

Methods:

#### `pivot(index: str, columns: str, value: str, agg: str) -> pandas.DataFrame`

A pivot table (built with `pandas.pivot_table`) of `value` aggregated by `agg`
over `index` (rows) x `columns` (columns).

- `agg` is either `"sum"` or `"count"`.
- **EVERY** missing `(index, column)` combination — a combination that does not
  occur in the data — MUST be filled with `0` (the integer zero), **NOT** `NaN`.
- For both `agg == "count"` and `agg == "sum"`, every cell MUST be a
  Python/NumPy **integer** (an integer dtype column) — no floats, no `NaN`
  anywhere in the result.
- The result's **columns** are sorted in ascending order; the result's **index**
  is sorted in ascending order.

#### `totals(index: str, columns: str, value: str, agg: str) -> pandas.DataFrame`

The same pivot as `pivot(...)` plus:

- one extra **row** labelled exactly `"Total"` holding the column marginal sums,
- one extra **column** labelled exactly `"Total"` holding the row marginal sums.

Use the exact label `"Total"` (a string) for both margins — **not** pandas'
default `"All"`. The bottom-right `("Total", "Total")` cell is the grand total.

#### `top_n(index: str, value: str, n: int) -> list[tuple]`

- Group the rows by `index`, **SUM** `value` within each group.
- Return the top `n` groups as `(index_label, total)` tuples.
- Sort by `total` **DESCENDING**; break ties by `index_label` **ASCENDING**.
- Return at most `n` tuples (fewer if there are fewer than `n` groups).

---

## Notes

- `index` / `columns` / `value` are column names present in the records.
- All aggregated values in the test data are non-negative integers.
- Determinism: the same records always yield identical results.
- The grader imports only from `report.py`; internal module layout is up to you.
