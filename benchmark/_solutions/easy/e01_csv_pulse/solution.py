"""Gold reference for easy/e01_csv_pulse — per-column CSV statistics (stdlib only)."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys


def _to_float(value: str):
    """Return the float value of a non-empty cell, or None if it is not numeric."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _column_values(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    """Group cell strings by column name, preserving row order."""
    columns: dict[str, list[str]] = {}
    for row in rows:
        for key, val in row.items():
            columns.setdefault(key, []).append(val)
    return columns


def _numeric_or_none(cells: list[str]):
    """Return the numeric values if the column is numeric (see TASK.md), else None.

    A column is numeric iff it has >=1 non-empty value and every non-empty value
    parses as a float. Empty cells are skipped.
    """
    numbers: list[float] = []
    for cell in cells:
        if cell is None or cell == "":
            continue
        parsed = _to_float(cell)
        if parsed is None:
            return None  # a non-empty, non-numeric value disqualifies the column
        numbers.append(parsed)
    return numbers if numbers else None


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    """Return ``{column: {count, mean, median, min, max, std}}`` for numeric columns."""
    result: dict[str, dict] = {}
    for name, cells in _column_values(rows).items():
        numbers = _numeric_or_none(cells)
        if numbers is None:
            continue
        result[name] = {
            "count": len(numbers),
            "mean": statistics.fmean(numbers),
            "median": statistics.median(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "std": statistics.pstdev(numbers),  # population std, ddof=0
        }
    return result


def _read_rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-column statistics for a CSV file.")
    parser.add_argument("csv_path")
    parser.add_argument("--column", default=None)
    args = parser.parse_args(argv)

    stats = summarize(_read_rows(args.csv_path))
    if args.column is None:
        print(json.dumps(stats, indent=2))
        return 0
    if args.column not in stats:
        print(f"error: column {args.column!r} is missing or not numeric", file=sys.stderr)
        return 1
    print(json.dumps(stats[args.column], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
