# Easy 01 — `csv_pulse`: per-column statistics for a CSV

**Created:** 2026-06-15 · **Category:** easy · **Weight:** 1

Implement a small, single-file CSV statistics tool. Write your solution as
`solution.py`. Use the **standard library only** (e.g. `csv`, `statistics`,
`json`, `argparse`). Do not read any file outside the one passed on the CLI.

## Public contract (must match exactly)

```python
def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    ...
```

`rows` is a list of records as produced by `csv.DictReader` (every value is a
string; keys are the column names).

A column is **numeric** iff it has at least one non-empty value and *every*
non-empty value parses as a `float`. Empty strings (`""`) are treated as missing
and skipped. Non-numeric columns (any non-empty value that does not parse as a
float) are **omitted** from the result entirely.

For each numeric column return a dict with these keys (all floats except
`count`), computed over its non-empty numeric values:

| key | meaning |
|---|---|
| `count` | number of numeric (non-empty) values — an `int` |
| `mean` | arithmetic mean |
| `median` | median (average of the two middle values for an even count) |
| `min` | minimum |
| `max` | maximum |
| `std` | **population** standard deviation (ddof = 0) |

Order of columns in the returned dict does not matter. A column with zero numeric
values is omitted.

## CLI contract

```
python solution.py <csv_path> [--column NAME]
```

* With no `--column`: print `json.dumps(summarize(rows), indent=2)` to **stdout**
  and exit `0`.
* With `--column NAME`: print the JSON stats dict for that one column to stdout and
  exit `0`. If `NAME` is missing or not numeric, print an error to **stderr** and
  exit with a **non-zero** status (do not print stats to stdout).

The CSV is read with `csv.DictReader` (first row is the header).

## Notes

* Determinism: identical input ⇒ identical output.
* Floats are compared by the grader with a tolerance, so do not round.
