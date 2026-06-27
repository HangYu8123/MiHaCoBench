"""
Mega ETL pipeline — 20-step chain.
Usage: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step_1_parse(data):
    """Read `values` from input; convert each integer to float."""
    return [float(v) for v in data["values"]]


def step_2_add_const(data):
    """Add 7.0 to every element."""
    return [x + 7.0 for x in data]


def step_3_double(data):
    """Multiply every element by 2."""
    return [x * 2 for x in data]


def step_4_mod(data):
    """Apply modulo 11 to every element (floating-point %)."""
    return [x % 11 for x in data]


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
    current_max = None
    for x in data:
        if current_max is None or x > current_max:
            current_max = x
        result.append(current_max)
    return result


def step_8_prefix_min(data):
    """Running minimum from right: result[i] = min(data[i], data[i+1], ..., data[n-1])."""
    n = len(data)
    result = [0.0] * n
    current_min = None
    for i in range(n - 1, -1, -1):
        if current_min is None or data[i] < current_min:
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
    """Min-max normalization to [0, 1]. If max == min, all elements become 0.0."""
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(x - mn) / (mx - mn) for x in data]


def step_13_scale(data):
    """Multiply every element by 1000."""
    return [x * 1000 for x in data]


def step_14_round3(data):
    """Round every element to 3 decimal places."""
    return [round(x, 3) for x in data]


def step_15_moving_avg_3(data):
    """Trailing 3-element moving average with boundary handling."""
    result = []
    for k in range(len(data)):
        if k == 0:
            result.append(data[0])
        elif k == 1:
            result.append((data[0] + data[1]) / 2.0)
        else:
            result.append((data[k - 2] + data[k - 1] + data[k]) / 3.0)
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
        "count": len(data),
    }


STEP_FUNCTIONS = {
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Compute provenance BEFORE reading content for processing
    provenance = compute_provenance(in_path)

    # Read input
    with open(in_path, "r") as f:
        in_obj = json.load(f)

    # Step 1 reads the raw input object; all other steps read in_obj["data"]
    if step == 1:
        input_data = in_obj
    else:
        input_data = in_obj["data"]

    # Run the step
    if step not in STEP_FUNCTIONS:
        print(f"Unknown step: {step}", file=sys.stderr)
        sys.exit(1)

    result = STEP_FUNCTIONS[step](input_data)

    # Write output
    out_obj = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(out_obj, f)


if __name__ == "__main__":
    main()
