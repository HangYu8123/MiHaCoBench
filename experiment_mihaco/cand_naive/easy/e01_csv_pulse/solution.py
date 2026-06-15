"""csv_pulse: per-column statistics for a CSV file.

Public API
----------
summarize(rows) -> dict[str, dict]
    Compute per-column statistics over a list of csv.DictReader records.

CLI
---
    python solution.py <csv_path> [--column NAME]
"""

import argparse
import csv
import json
import math
import statistics
import sys
from typing import Optional


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    """Compute per-column statistics for numeric columns in *rows*.

    Parameters
    ----------
    rows:
        A list of records as produced by ``csv.DictReader``.  Every value is a
        string; keys are column names.

    Returns
    -------
    dict
        Mapping of column name -> stats dict.  Only **numeric** columns are
        included.  A column is numeric iff it has at least one non-empty value
        and every non-empty value parses as ``float``.  Empty strings are
        treated as missing and skipped.  Columns with zero numeric values are
        also omitted.

        Each stats dict contains:

        * ``count`` (int)   -- number of non-empty numeric values
        * ``mean``  (float) -- arithmetic mean
        * ``median``(float) -- median (average of two middles for even count)
        * ``min``   (float) -- minimum value
        * ``max``   (float) -- maximum value
        * ``std``   (float) -- population standard deviation (ddof=0)
    """
    if not rows:
        return {}

    # Collect column names in order of first appearance.
    columns: list[str] = list(rows[0].keys())

    result: dict[str, dict] = {}

    for col in columns:
        numeric_values: list[float] = []
        is_numeric = True  # Assume numeric until proven otherwise.

        for row in rows:
            raw = row.get(col, "")
            if raw == "":
                # Missing / empty — skip but do not invalidate the column.
                continue
            try:
                numeric_values.append(float(raw))
            except ValueError:
                # At least one non-empty value is not a float.
                is_numeric = False
                break

        if not is_numeric or len(numeric_values) == 0:
            # Non-numeric column or no values at all — omit.
            continue

        count = len(numeric_values)
        mean = sum(numeric_values) / count

        sorted_vals = sorted(numeric_values)
        mid = count // 2
        if count % 2 == 1:
            median = float(sorted_vals[mid])
        else:
            median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0

        col_min = float(min(numeric_values))
        col_max = float(max(numeric_values))

        # Population standard deviation (ddof=0).
        variance = sum((x - mean) ** 2 for x in numeric_values) / count
        std = math.sqrt(variance)

        result[col] = {
            "count": count,
            "mean": mean,
            "median": median,
            "min": col_min,
            "max": col_max,
            "std": std,
        }

    return result


def _load_rows(csv_path: str) -> list[dict[str, str]]:
    """Read *csv_path* with ``csv.DictReader`` and return all rows as a list."""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the CLI.

    Parameters
    ----------
    argv:
        Argument list (defaults to ``sys.argv[1:]`` when *None*).

    Returns
    -------
    int
        Exit status: 0 on success, non-zero on error.
    """
    parser = argparse.ArgumentParser(
        description="Print per-column statistics for a CSV file."
    )
    parser.add_argument("csv_path", help="Path to the CSV file.")
    parser.add_argument(
        "--column",
        metavar="NAME",
        default=None,
        help="If given, print stats only for this column.",
    )
    args = parser.parse_args(argv)

    try:
        rows = _load_rows(args.csv_path)
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return 1

    stats = summarize(rows)

    if args.column is None:
        print(json.dumps(stats, indent=2))
        return 0

    # --column mode
    col_name = args.column
    if col_name not in stats:
        print(
            f"Error: column '{col_name}' is missing or not numeric.",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(stats[col_name], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
