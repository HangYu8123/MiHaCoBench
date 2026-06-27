"""csv_pulse: per-column statistics for a CSV (stdlib only)."""

import csv
import json
import math
import argparse
import sys


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    """Compute per-column statistics for numeric columns.

    Args:
        rows: list of records as produced by csv.DictReader

    Returns:
        dict mapping column name -> stats dict for numeric columns only.
    """
    if not rows:
        return {}

    columns = list(rows[0].keys())
    result = {}

    for col in columns:
        numeric_values = []
        is_numeric = True

        for row in rows:
            val = row.get(col, "")
            if val == "":
                # treat as missing, skip
                continue
            try:
                float_val = float(val)
                numeric_values.append(float_val)
            except (ValueError, TypeError):
                is_numeric = False
                break

        if not is_numeric or len(numeric_values) == 0:
            continue

        n = len(numeric_values)
        mean = sum(numeric_values) / n

        sorted_vals = sorted(numeric_values)
        if n % 2 == 1:
            median = sorted_vals[n // 2]
        else:
            median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

        min_val = sorted_vals[0]
        max_val = sorted_vals[-1]

        # population std (ddof=0)
        variance = sum((v - mean) ** 2 for v in numeric_values) / n
        std = math.sqrt(variance)

        result[col] = {
            "count": n,
            "mean": mean,
            "median": median,
            "min": min_val,
            "max": max_val,
            "std": std,
        }

    return result


def main():
    parser = argparse.ArgumentParser(description="CSV per-column statistics")
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument("--column", help="Show stats for a single column", default=None)
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    stats = summarize(rows)

    if args.column is None:
        print(json.dumps(stats, indent=2))
        sys.exit(0)
    else:
        col = args.column
        if col not in stats:
            print(f"Error: column '{col}' is missing or not numeric.", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(stats[col], indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
