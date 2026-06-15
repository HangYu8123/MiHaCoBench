# Complex 05 — `etl_framework`: YAML-driven ETL Pipeline

**Created:** 2026-06-15 · **Category:** complex · **Weight:** 5

Implement a YAML-driven ETL (Extract-Transform-Load) framework. Structure your
solution as multiple modules:

```
config.py       — parse a YAML pipeline spec into dataclasses
transforms.py   — Transform base class + FilterRows, RenameColumns, DeriveColumn,
                  Aggregate subclasses; all registered in a transform registry
loaders.py      — SQLAlchemy loader that persists a DataFrame to an in-memory DB
pipeline.py     — Public facade class Pipeline (the grader imports THIS file only)
```

Use **pandas**, **SQLAlchemy 2.0**, and **pyyaml**. Use an in-memory SQLite
database (`"sqlite:///:memory:"`) — no external server required.

## Public contract (in `pipeline.py`)

The grader imports `pipeline.py` and uses only these names:

```python
class Pipeline:
    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: str | None = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline.

        ``data_dir`` is prepended to a relative CSV path in the extract section.
        If the CSV path is already absolute, ``data_dir`` is ignored.
        """

    def run(self) -> pandas.DataFrame:
        """Execute the full pipeline: extract → transform → load → return.

        Reads the CSV specified in ``extract``, applies each transform in order,
        loads the final DataFrame into the SQLAlchemy table named in ``load``,
        and returns the final DataFrame.

        Raises ``ValueError`` if a column required by a transform step is missing
        from the DataFrame at the point where that step is applied.
        """

    def query(self, sql: str) -> list[dict]:
        """Execute a raw SQL string against the loaded table.

        Returns a list of row dicts (column name → Python value). ``run()``
        must have been called first; raises ``RuntimeError`` if not.
        """
```

## YAML pipeline spec shape

```yaml
extract:
  csv: path/to/file.csv       # relative path (resolved against data_dir) or absolute

transforms:
  - op: filter
    column: <col>             # column to compare
    op_kind: ">"              # one of: ">", ">=", "<", "<=", "==", "!="
    value: <number or string> # compared against the column's values

  - op: rename
    mapping:
      old_name: new_name      # one or more column renames

  - op: derive
    column: <new_col>         # name of the new column to add
    expr: "<pandas expression>" # evaluated with df.eval(expr); may reference existing cols

  - op: aggregate
    group_by:
      - <col>                 # one or more columns to group by
    agg:
      <col>: <func>           # aggregation: col → function name (sum, mean, min, max, count)

load:
  table: <table_name>         # name of the SQLAlchemy table to write to
```

### Transform semantics

- **filter**: Keep only rows where `column op_kind value` is true.
  Numeric `value` fields are cast to `float` for comparison.
- **rename**: Rename columns according to `mapping`; missing keys are silently skipped.
- **derive**: Add a new column using `df.eval(expr)`.
- **aggregate**: Group by the listed columns and aggregate. After aggregation the
  DataFrame contains only the `group_by` columns plus the aggregated columns.
  The result is reset-indexed.

### Validation

After loading the CSV but before applying transforms, raise `ValueError` if any
column named in the pipeline spec (filter column, rename source key, derive expr
variable references that match existing column names, aggregate group_by or agg
keys) does not exist in the DataFrame. Specifically:

- **filter**: raise `ValueError` if the `column` field is not in the DataFrame.
- **aggregate**: raise `ValueError` if any column in `group_by` or `agg` keys is
  not in the DataFrame at the time the aggregate step is applied.

## Committed input data

The grader uses the file `data/sales.csv` committed alongside this task.

### Column descriptions

| Column | Type | Description |
|---|---|---|
| `order_id` | int | Unique order identifier |
| `region` | str | Sales region: north, south, east, west |
| `product` | str | Product name: apple, banana, cherry |
| `quantity` | int | Units ordered |
| `unit_price` | float | Price per unit in USD |
| `discount` | float | Fractional discount (0.0–1.0) |

The CSV has 15 rows (order_ids 1–15).

## Notes

- Load must use SQLAlchemy with `if_exists="replace"` so repeated `run()` calls
  are idempotent.
- `query()` must raise `RuntimeError` if called before `run()`.
- Float columns are compared by the grader with tolerance; use `gu.close`.
- Determinism: identical spec + CSV ⇒ identical output.
