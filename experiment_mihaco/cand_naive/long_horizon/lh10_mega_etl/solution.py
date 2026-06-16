"""
20-step ETL pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the input file bytes."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step_1_parse(data):
    """Read 'values' from input; convert each integer to float."""
    return [float(x) for x in data["values"]]


def step_2_add_const(data):
    """Add 7.0 to every element."""
    return [x + 7.0 for x in data]


def step_3_double(data):
    """Multiply every element by 2."""
    return [x * 2.0 for x in data]


def step_4_mod(data):
    """Apply modulo 11 to every element (floating-point %)."""
    return [x % 11.0 for x in data]


def step_5_scale_by_index(data):
    """Multiply each element by its 1-based position."""
    return [x * (i + 1) for i, x in enumerate(data)]


def step_6_cumsum(data):
    """Running cumulative sum."""
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step_7_prefix_max(data):
    """Running maximum from left."""
    result = []
    current_max = float("-inf")
    for x in data:
        if x > current_max:
            current_max = x
        result.append(current_max)
    return result


def step_8_prefix_min(data):
    """Running minimum from right (element k = min of elements k..end)."""
    n = len(data)
    result = [0.0] * n
    current_min = float("inf")
    for i in range(n - 1, -1, -1):
        if data[i] < current_min:
            current_min = data[i]
        result[i] = current_min
    return result


def step_9_diffs(data):
    """Consecutive differences: result[i] = data[i+1] - data[i]."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_10_abs(data):
    """Absolute value of every element."""
    return [abs(x) for x in data]


def step_11_square(data):
    """Square every element."""
    return [x * x for x in data]


def step_12_normalize_minmax(data):
    """Min-max normalization to [0, 1]."""
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0 for _ in data]
    return [(x - mn) / (mx - mn) for x in data]


def step_13_scale(data):
    """Multiply every element by 1000."""
    return [x * 1000.0 for x in data]


def step_14_round3(data):
    """Round every element to 3 decimal places."""
    return [round(x, 3) for x in data]


def step_15_moving_avg_3(data):
    """Trailing 3-element moving average with smaller window at boundaries."""
    result = []
    for i, x in enumerate(data):
        if i == 0:
            result.append(x)
        elif i == 1:
            result.append((data[0] + data[1]) / 2.0)
        else:
            result.append((data[i - 2] + data[i - 1] + data[i]) / 3.0)
    return result


def step_16_filter_gt_mean(data):
    """Keep only elements strictly greater than the arithmetic mean."""
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step_17_sort_desc(data):
    """Sort in descending order."""
    return sorted(data, reverse=True)


def step_18_dedupe(data):
    """Remove duplicate values (keep first occurrence in current order)."""
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step_19_top_k(data):
    """Keep the first 5 elements."""
    return data[:5]


def step_20_aggregate(data):
    """Compute summary statistics over the 5 values."""
    return {
        "sum": float(sum(data)),
        "mean": float(sum(data) / len(data)),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": int(len(data)),
    }


STEPS = {
    1: step_1_parse,
    2: step_2_add_const,
    3: step_3_double,
    4: step_4_mod,
    5: step_5_scale_by_index,
    6: step_6_cumsum,
    7: step_7_prefix_max,
    8: step_8_prefix_min,
    9: step_9_diffs,
    10: step_10_abs,
    11: step_11_square,
    12: step_12_normalize_minmax,
    13: step_13_scale,
    14: step_14_round3,
    15: step_15_moving_avg_3,
    16: step_16_filter_gt_mean,
    17: step_17_sort_desc,
    18: step_18_dedupe,
    19: step_19_top_k,
    20: step_20_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="20-step ETL pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-20)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_num not in STEPS:
        print(f"Error: step {step_num} is not defined (must be 1-20)", file=sys.stderr)
        sys.exit(1)

    # Compute provenance BEFORE reading data (from the raw bytes)
    provenance = compute_provenance(in_path)

    # Read input JSON
    with open(in_path, "r") as f:
        in_data = json.load(f)

    # For step 1, input is the raw input.json with 'values' key.
    # For steps 2-20, input is the output of the previous step with 'data' key.
    if step_num == 1:
        data = in_data
    else:
        data = in_data["data"]

    # Run the step
    step_fn = STEPS[step_num]
    result = step_fn(data)

    # Write output
    out_obj = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(out_obj, f)

    print(f"Step {step_num} complete. Output written to {out_path}")


if __name__ == "__main__":
    main()
