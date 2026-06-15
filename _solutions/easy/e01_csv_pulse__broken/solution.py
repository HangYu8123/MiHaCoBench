"""Deliberately-broken reference for easy/e01_csv_pulse.

Two planted defects so the grader must catch it:
  1. Uses SAMPLE std (ddof=1) instead of population std → wrong `std`.
  2. Mishandles empty cells / mixed columns relative to the spec.
This MUST fail the grader (proves the grader discriminates).
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    columns: dict[str, list[str]] = {}
    for row in rows:
        for key, val in row.items():
            columns.setdefault(key, []).append(val)

    result: dict[str, dict] = {}
    for name, cells in columns.items():
        numbers = []
        ok = True
        for cell in cells:
            try:
                numbers.append(float(cell))  # BUG: empty "" raises / not skipped
            except (TypeError, ValueError):
                if cell == "":
                    continue  # half-handles empty, but mixing remains buggy below
                ok = False
                break
        if not ok or not numbers:
            continue
        result[name] = {
            "count": len(numbers),
            "mean": sum(numbers) / len(numbers),
            "median": statistics.median(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "std": statistics.stdev(numbers) if len(numbers) > 1 else 0.0,  # BUG: sample std
        }
    return result


def _read_rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--column", default=None)
    args = parser.parse_args(argv)
    stats = summarize(_read_rows(args.csv_path))
    if args.column is None:
        print(json.dumps(stats, indent=2))
        return 0
    if args.column not in stats:
        print("error", file=sys.stderr)
        return 1
    print(json.dumps(stats[args.column], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
