"""
20-step ETL pipeline.

CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Output JSON: {"step": K, "data": <result>, "provenance": "<sha256_hex>"}
"""

import argparse
import hashlib
import itertools
import json
import sys


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step_parse(raw):
    """Step 1: read values from input.json; convert each integer to float."""
    return [float(x) for x in raw["values"]]


def step_add_const(data):
    """Step 2: add 7.0 to every element."""
    return [x + 7.0 for x in data]


def step_double(data):
    """Step 3: multiply every element by 2."""
    return [x * 2 for x in data]


def step_mod(data):
    """Step 4: apply modulo 11 to every element (floating-point %)."""
    return [x % 11 for x in data]


def step_scale_by_index(data):
    """Step 5: multiply each element by its 1-based position (i+1)."""
    return [x * (i + 1) for i, x in enumerate(data)]


def step_cumsum(data):
    """Step 6: running cumulative sum."""
    return list(itertools.accumulate(data))


def step_prefix_max(data):
    """Step 7: running maximum from left."""
    return list(itertools.accumulate(data, max))


def step_prefix_min(data):
    """Step 8: running minimum from RIGHT (suffix minimum).
    result[i] = min(data[i], data[i+1], ..., data[n-1])
    """
    n = len(data)
    result = [0.0] * n
    result[-1] = data[-1]
    for i in range(n - 2, -1, -1):
        result[i] = min(result[i + 1], data[i])
    return result


def step_diffs(data):
    """Step 9: consecutive differences; result length = len(data) - 1."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_abs(data):
    """Step 10: absolute value of every element."""
    return [abs(x) for x in data]


def step_square(data):
    """Step 11: square every element."""
    return [x * x for x in data]


def step_normalize_minmax(data):
    """Step 12: min-max normalization to [0, 1]. If max==min, return all 0.0."""
    lo = min(data)
    hi = max(data)
    if hi == lo:
        return [0.0 for _ in data]
    return [(x - lo) / (hi - lo) for x in data]


def step_scale(data):
    """Step 13: multiply every element by 1000."""
    return [x * 1000 for x in data]


def step_round3(data):
    """Step 14: round every element to 3 decimal places."""
    return [round(x, 3) for x in data]


def step_moving_avg_3(data):
    """Step 15: trailing 3-element moving average with boundary handling.
    element 0 stays as-is, element 1 = avg(0..1), element k>=2 = avg(k-2, k-1, k).
    """
    result = []
    for i in range(len(data)):
        window = data[max(0, i - 2): i + 1]
        result.append(sum(window) / len(window))
    return result


def step_filter_gt_mean(data):
    """Step 16: keep only elements strictly greater than the arithmetic mean."""
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step_sort_desc(data):
    """Step 17: sort in descending order."""
    return sorted(data, reverse=True)


def step_dedupe(data):
    """Step 18: remove duplicate values, preserving first-occurrence order."""
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step_top_k(data):
    """Step 19: keep the first 5 elements."""
    return data[:5]


def step_aggregate(data):
    """Step 20: compute summary statistics over the 5 values."""
    d = data
    return {
        "sum": float(sum(d)),
        "mean": float(sum(d) / len(d)),
        "min": float(min(d)),
        "max": float(max(d)),
        "count": int(len(d)),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

STEPS = {
    1: step_parse,
    2: step_add_const,
    3: step_double,
    4: step_mod,
    5: step_scale_by_index,
    6: step_cumsum,
    7: step_prefix_max,
    8: step_prefix_min,
    9: step_diffs,
    10: step_abs,
    11: step_square,
    12: step_normalize_minmax,
    13: step_scale,
    14: step_round3,
    15: step_moving_avg_3,
    16: step_filter_gt_mean,
    17: step_sort_desc,
    18: step_dedupe,
    19: step_top_k,
    20: step_aggregate,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="20-step ETL pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-20)")
    parser.add_argument("--in", dest="input", required=True, help="Path to input JSON file")
    parser.add_argument("--out", required=True, help="Path to output JSON file")
    args = parser.parse_args()

    in_path = args.input
    out_path = args.out
    step_k = args.step

    # Read raw bytes for provenance FIRST (before any JSON parsing).
    with open(in_path, "rb") as fh:
        raw_bytes = fh.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse the input JSON.
    raw = json.loads(raw_bytes)

    # Extract the data payload:
    # Step 1 reads {"values": [...]} from the original input file.
    # Steps 2-20 read {"step": K-1, "data": [...], "provenance": "..."} from prior step output.
    if step_k == 1:
        payload = raw  # pass the whole dict; step_parse will extract "values"
    else:
        payload = raw["data"]

    if step_k not in STEPS:
        print(f"Unknown step: {step_k}", file=sys.stderr)
        sys.exit(1)

    result = STEPS[step_k](payload)

    output = {
        "step": step_k,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as fh:
        json.dump(output, fh)


if __name__ == "__main__":
    main()
