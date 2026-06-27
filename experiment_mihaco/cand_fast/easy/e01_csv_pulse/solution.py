import csv
import json
import math
import argparse
import sys


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    """
    Given a list of row dicts (as produced by csv.DictReader),
    return a dict mapping each numeric column name to its statistics.

    A column is numeric iff it has >= 1 non-empty value and every
    non-empty value parses as float. Empty strings are skipped.
    Non-numeric columns are omitted entirely.
    """
    if not rows:
        return {}

    # Collect all column names from all rows (preserve order from first row)
    columns = list(rows[0].keys())

    result = {}

    for col in columns:
        # Collect non-empty values for this column
        non_empty = []
        for row in rows:
            val = row.get(col, "")
            if val != "":
                non_empty.append(val)

        # Skip column if no non-empty values
        if not non_empty:
            continue

        # Try to parse all non-empty values as float
        numeric_vals = []
        is_numeric = True
        for val in non_empty:
            try:
                numeric_vals.append(float(val))
            except ValueError:
                is_numeric = False
                break

        # Skip column if any non-empty value is non-numeric
        if not is_numeric:
            continue

        # Compute statistics over numeric_vals
        n = len(numeric_vals)
        count = n

        # mean
        mean = sum(numeric_vals) / n

        # min, max
        min_val = min(numeric_vals)
        max_val = max(numeric_vals)

        # median (sort, then pick middle or average two middles)
        sorted_vals = sorted(numeric_vals)
        if n % 2 == 1:
            median = sorted_vals[n // 2]
        else:
            median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

        # population std (ddof=0): sqrt(sum((x - mean)^2) / n)
        std = math.sqrt(sum((x - mean) ** 2 for x in numeric_vals) / n)

        result[col] = {
            "count": count,
            "mean": mean,
            "median": median,
            "min": min_val,
            "max": max_val,
            "std": std,
        }

    return result


def main():
    parser = argparse.ArgumentParser(description="CSV column statistics tool")
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument("--column", default=None, help="Column name to report")
    args = parser.parse_args()

    with open(args.csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    result = summarize(rows)

    if args.column is None:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        col = args.column
        if col not in result:
            sys.stderr.write(
                f"Error: column '{col}' is missing or not numeric.\n"
            )
            sys.exit(1)
        print(json.dumps(result[col], indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
