"""
solution.py — e01_csv_pulse
Per-column statistics for a CSV file.

Public contract:
    def summarize(rows: list[dict[str, str]]) -> dict[str, dict]: ...
"""

import argparse
import csv
import json
import math
import sys


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    """
    Given a list of row dicts (as produced by csv.DictReader), return a dict
    mapping each numeric column name to its stats dict.

    A column is numeric iff it has at least one non-empty value and every
    non-empty value parses as float. Empty strings are treated as missing and
    skipped. Non-numeric and all-empty columns are omitted from the result.

    Stats dict keys:
        count  : int   — number of non-empty numeric values
        mean   : float — arithmetic mean
        median : float — median (average of two middle values for even count)
        min    : float — minimum
        max    : float — maximum
        std    : float — population standard deviation (ddof=0)
    """
    if not rows:
        return {}

    # Collect column names in insertion order from the first row.
    # csv.DictReader always yields a fixed header so all rows share the same keys.
    columns = list(rows[0].keys())

    result = {}

    for col in columns:
        numeric_vals: list[float] = []
        is_numeric = True

        for row in rows:
            raw = row.get(col, "")
            if raw == "":
                # Missing / empty — skip
                continue
            try:
                numeric_vals.append(float(raw))
            except (ValueError, TypeError):
                is_numeric = False
                break  # Column is non-numeric; skip it entirely

        if not is_numeric:
            continue
        if len(numeric_vals) == 0:
            # All-empty column — omit
            continue

        vals = numeric_vals
        n = len(vals)
        count = int(n)  # Must be int, not float

        total = sum(vals)
        mean = total / n

        sorted_vals = sorted(vals)
        if n % 2 == 1:
            median = sorted_vals[n // 2]
        else:
            median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

        minimum = sorted_vals[0]
        maximum = sorted_vals[-1]

        # Population standard deviation (ddof=0)
        variance = sum((x - mean) ** 2 for x in vals) / n
        std = math.sqrt(variance)

        result[col] = {
            "count": count,
            "mean": mean,
            "median": median,
            "min": minimum,
            "max": maximum,
            "std": std,
        }

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute per-column statistics for a CSV file."
    )
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument("--column", metavar="NAME", help="Print stats for one column only")
    args = parser.parse_args()

    with open(args.csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    result = summarize(rows)

    if args.column is None:
        # Print all stats
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        col_name = args.column
        if col_name not in result:
            print(
                f"Error: column '{col_name}' is missing or not numeric.",
                file=sys.stderr,
            )
            sys.exit(1)
        # Column is in result — print its stats
        print(json.dumps(result[col_name], indent=2))
        sys.exit(0)
