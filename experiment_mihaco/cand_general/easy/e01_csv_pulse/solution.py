"""csv_pulse — per-column statistics for a CSV file.

Public contract
---------------
    summarize(rows) -> dict[str, dict]

CLI
---
    python solution.py <csv_path> [--column NAME]

Standard library only: csv, json, argparse, sys, statistics.
"""

import argparse
import csv
import json
import statistics
import sys


def summarize(rows: list[dict[str, str]]) -> "dict[str, dict]":
    """Compute per-column statistics for numeric columns.

    Parameters
    ----------
    rows:
        List of records as produced by csv.DictReader.  Every value is a
        string; keys are the column names.

    Returns
    -------
    A dict mapping each *numeric* column name to a stats dict with keys:
        count  (int)   — number of non-empty numeric values
        mean   (float) — arithmetic mean
        median (float) — median (avg of two middle values for even count)
        min    (float) — minimum
        max    (float) — maximum
        std    (float) — population standard deviation (ddof=0)

    A column is numeric iff every non-empty value parses as float.  Empty
    strings ("") are treated as missing and skipped.  Non-numeric columns and
    columns with zero numeric values are omitted from the result.
    """
    if not rows:
        return {}

    columns = list(rows[0].keys())
    result: dict[str, dict] = {}

    for col in columns:
        # Collect non-empty values for this column.
        # csv.DictReader may produce None for missing fields (short rows) so
        # we guard against that: treat None like an empty cell.
        raw_candidates = []
        for row in rows:
            val = row.get(col)  # returns None if key absent (short row)
            if val is None:
                continue
            if val != "":
                raw_candidates.append(val)

        # No non-empty values — omit column.
        if not raw_candidates:
            continue

        # Attempt to parse every candidate as float.
        values: list[float] = []
        numeric = True
        for v in raw_candidates:
            try:
                values.append(float(v))
            except (ValueError, TypeError):
                numeric = False
                break

        if not numeric:
            continue

        # Compute statistics over the parsed float values.
        count = len(values)  # int
        mean = sum(values) / count  # float; count > 0 guaranteed
        median = statistics.median(values)  # averages two midpoints for even n
        col_min = float(min(values))
        col_max = float(max(values))
        std = statistics.pstdev(values)  # population std dev, ddof=0

        result[col] = {
            "count": count,
            "mean": mean,
            "median": median,
            "min": col_min,
            "max": col_max,
            "std": std,
        }

    return result


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compute per-column statistics for a CSV file."
    )
    parser.add_argument("csv_path", help="Path to the CSV file.")
    parser.add_argument(
        "--column",
        metavar="NAME",
        default=None,
        help="If given, print stats for this column only.",
    )
    args = parser.parse_args()

    # Open with newline='' as recommended by the csv module to avoid
    # spurious \r characters on Windows-originated files.
    try:
        with open(args.csv_path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        print(f"Error opening file: {exc}", file=sys.stderr)
        sys.exit(1)

    result = summarize(rows)

    if args.column is None:
        # Print full summary.
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Single-column mode.
    if args.column in result:
        print(json.dumps(result[args.column], indent=2))
        sys.exit(0)
    else:
        print(
            f"Error: column '{args.column}' is not present or is not numeric.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
