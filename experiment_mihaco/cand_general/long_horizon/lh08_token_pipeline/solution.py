"""
16-step token pipeline.

CLI: python solution.py --step K --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import itertools
import json


def step_parse(arr):
    """Step 1: cast each integer to float."""
    return [float(x) for x in arr]


def step_add_const(arr):
    """Step 2: add 1 to every element."""
    return [x + 1.0 for x in arr]


def step_double(arr):
    """Step 3: multiply every element by 2."""
    return [x * 2 for x in arr]


def step_mod(arr):
    """Step 4: apply % 5 (Python modulo) to every element."""
    return [x % 5 for x in arr]


def step_scale_by_index(arr):
    """Step 5: multiply each element by its zero-based index."""
    return [v * i for i, v in enumerate(arr)]


def step_cumsum(arr):
    """Step 6: cumulative sums (running totals)."""
    return list(itertools.accumulate(arr))


def step_prefix_max(arr):
    """Step 7: running prefix maximum."""
    return list(itertools.accumulate(arr, max))


def step_diffs(arr):
    """Step 8: consecutive differences; output length = input length - 1."""
    return [arr[i + 1] - arr[i] for i in range(len(arr) - 1)]


def step_abs(arr):
    """Step 9: abs() every element."""
    return [abs(x) for x in arr]


def step_square(arr):
    """Step 10: square every element."""
    return [x * x for x in arr]


def step_normalize_minmax(arr):
    """Step 11: min-max normalisation; all zeros if all values equal."""
    mn = min(arr)
    mx = max(arr)
    if mx == mn:
        return [0.0] * len(arr)
    return [(x - mn) / (mx - mn) for x in arr]


def step_scale(arr):
    """Step 12: multiply every element by 10."""
    return [x * 10 for x in arr]


def step_round3(arr):
    """Step 13: round every element to 3 decimal places."""
    return [round(x, 3) for x in arr]


def step_sort_asc(arr):
    """Step 14: sort the list ascending."""
    return sorted(arr)


def step_dedupe(arr):
    """Step 15: remove consecutive duplicate values (keep first)."""
    return [k for k, _ in itertools.groupby(arr)]


def step_aggregate(arr):
    """Step 16: produce summary dict."""
    s = sum(arr)
    n = len(arr)
    return {
        "sum": s,
        "mean": s / n,
        "max": max(arr),
        "min": min(arr),
        "count": int(n),
    }


STEP_FUNCS = {
    1: step_parse,
    2: step_add_const,
    3: step_double,
    4: step_mod,
    5: step_scale_by_index,
    6: step_cumsum,
    7: step_prefix_max,
    8: step_diffs,
    9: step_abs,
    10: step_square,
    11: step_normalize_minmax,
    12: step_scale,
    13: step_round3,
    14: step_sort_asc,
    15: step_dedupe,
    16: step_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="16-step token pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-16)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    # Read raw bytes first for provenance computation (before any parsing)
    with open(args.in_path, "rb") as f:
        raw_bytes = f.read()

    # Compute provenance from the exact raw bytes of the input file
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON
    prev = json.loads(raw_bytes)

    # Extract input array
    if args.step == 1:
        arr = prev["values"]
    else:
        arr = prev["data"]

    # Apply step operation
    step_func = STEP_FUNCS[args.step]
    result = step_func(arr)

    # Write output
    output = {"step": args.step, "data": result, "provenance": provenance}
    with open(args.out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(output))


if __name__ == "__main__":
    main()
