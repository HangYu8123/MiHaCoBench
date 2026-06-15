"""csv_pulse: per-column statistics for a CSV file.

Public API:
    summarize(rows) -> dict[str, dict]

CLI:
    python solution.py <csv_path> [--column NAME]
"""

import argparse
import csv
import json
import statistics
import sys


def summarize(rows: list[dict[str, str]]) -> dict[str, dict]:
    """Compute per-column statistics for numeric columns.

    A column is numeric iff it has at least one non-empty value and every
    non-empty value parses as a float.  Empty strings are treated as missing
    and are skipped entirely.  Non-numeric columns are omitted from the result.

    Args:
        rows: List of records as produced by csv.DictReader.  Every value is a
              string; keys are the column names.

    Returns:
        A dict mapping each numeric column name to a stats dict with keys:
            count  (int)   - number of non-empty numeric values
            mean   (float) - arithmetic mean
            median (float) - median (average of two middle values for even n)
            min    (float) - minimum
            max    (float) - maximum
            std    (float) - population standard deviation (ddof=0)
    """
    if not rows:
        return {}

    # Collect all column names from the first row (preserves header order).
    column_names = list(rows[0].keys())

    result: dict[str, dict] = {}

    for col in column_names:
        numeric_values: list[float] = []
        is_numeric = True

        for row in rows:
            val = row.get(col, "")
            if val == "":
                # Missing / empty — skip without flagging the column.
                continue
            try:
                numeric_values.append(float(val))
            except ValueError:
                # Any non-empty, non-parseable value poisons the whole column.
                is_numeric = False
                break

        if not is_numeric:
            continue

        if len(numeric_values) == 0:
            # All values were empty — omit the column entirely.
            continue

        result[col] = {
            "count":  len(numeric_values),                      # int
            "mean":   statistics.mean(numeric_values),
            "median": statistics.median(numeric_values),
            "min":    min(numeric_values),
            "max":    max(numeric_values),
            "std":    statistics.pstdev(numeric_values),        # population, ddof=0
        }

    return result


def _parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute per-column statistics for a CSV file."
    )
    parser.add_argument("csv_path", help="Path to the input CSV file.")
    parser.add_argument(
        "--column",
        default=None,
        metavar="NAME",
        help="If given, print stats for this column only.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point for the CLI."""
    args = _parse_args(argv)

    with open(args.csv_path, newline="") as fh:
        rows = list(csv.DictReader(fh))

    result = summarize(rows)

    if args.column is None:
        # Full summary — all numeric columns.
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        # Single-column mode.
        if args.column not in result:
            print(
                f"Error: column '{args.column}' not found or not numeric",
                file=sys.stderr,
            )
            sys.exit(1)
        print(json.dumps(result[args.column], indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
