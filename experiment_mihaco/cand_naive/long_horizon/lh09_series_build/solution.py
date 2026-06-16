"""
Long-Horizon 09 — series_build (18 steps)

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import math
import sys


def compute_provenance(in_path: str) -> str:
    """Compute SHA-256 hex digest of the exact bytes of the input file."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step_1_parse_float(data):
    """Cast every integer in values to float. Input: dict with 'values' key."""
    values = data["values"]
    return [float(v) for v in values]


def step_2_double(data):
    """Multiply every element by 2."""
    return [v * 2.0 for v in data]


def step_3_add_const(data):
    """Add 2 to every element."""
    return [v + 2.0 for v in data]


def step_4_cumsum(data):
    """Replace with running cumulative sum (left to right)."""
    result = []
    running = 0.0
    for v in data:
        running += v
        result.append(running)
    return result


def step_5_mod(data):
    """Replace every element with v % 13 (Python modulo)."""
    return [v % 13 for v in data]


def step_6_scale_by_index(data):
    """Multiply every element by its 0-based index: v[i] *= i."""
    return [v * i for i, v in enumerate(data)]


def step_7_prefix_max(data):
    """Replace with running prefix maximum (left to right)."""
    result = []
    current_max = float('-inf')
    for v in data:
        if v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step_8_diffs(data):
    """Replace with consecutive differences: [s[1]-s[0], s[2]-s[1], ...]."""
    return [data[i+1] - data[i] for i in range(len(data) - 1)]


def step_9_abs(data):
    """Take the absolute value of every element."""
    return [abs(v) for v in data]


def step_10_filter_gt_mean(data):
    """Keep only elements strictly greater than the mean of the current list."""
    if len(data) == 0:
        return []
    mean = sum(data) / len(data)
    return [v for v in data if v > mean]


def step_11_square(data):
    """Square every element (v**2)."""
    return [v ** 2 for v in data]


def step_12_normalize_minmax(data):
    """Min-max normalize to [0, 1]. If all values equal, output all zeros."""
    if len(data) == 0:
        return []
    mn = min(data)
    mx = max(data)
    if mn == mx:
        return [0.0 for _ in data]
    return [(v - mn) / (mx - mn) for v in data]


def step_13_scale(data):
    """Multiply every element by 100."""
    return [v * 100.0 for v in data]


def step_14_round3(data):
    """Round every element to 3 decimal places."""
    return [round(v, 3) for v in data]


def step_15_moving_avg_3(data):
    """3-element moving average.
    Indices 0 and 1: output original value unchanged.
    Index i >= 2: (v[i-2] + v[i-1] + v[i]) / 3.
    """
    result = []
    for i, v in enumerate(data):
        if i < 2:
            result.append(v)
        else:
            result.append((data[i-2] + data[i-1] + data[i]) / 3.0)
    return result


def step_16_sort_desc(data):
    """Sort the list in descending order."""
    return sorted(data, reverse=True)


def step_17_top_k(data):
    """Keep only the first 6 elements (top-6 after descending sort)."""
    return data[:6]


def step_18_aggregate(data):
    """Compute sum, mean, count, min, max over the list."""
    if len(data) == 0:
        return {
            "sum": 0.0,
            "mean": 0.0,
            "count": 0,
            "min": 0.0,
            "max": 0.0
        }
    return {
        "sum": float(sum(data)),
        "mean": float(sum(data) / len(data)),
        "count": int(len(data)),
        "min": float(min(data)),
        "max": float(max(data))
    }


STEP_FUNCTIONS = {
    1: step_1_parse_float,
    2: step_2_double,
    3: step_3_add_const,
    4: step_4_cumsum,
    5: step_5_mod,
    6: step_6_scale_by_index,
    7: step_7_prefix_max,
    8: step_8_diffs,
    9: step_9_abs,
    10: step_10_filter_gt_mean,
    11: step_11_square,
    12: step_12_normalize_minmax,
    13: step_13_scale,
    14: step_14_round3,
    15: step_15_moving_avg_3,
    16: step_16_sort_desc,
    17: step_17_top_k,
    18: step_18_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="series_build pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-18)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step not in STEP_FUNCTIONS:
        print(f"Error: step {step} not in range 1-18", file=sys.stderr)
        sys.exit(1)

    # Compute provenance BEFORE reading data (same bytes)
    provenance = compute_provenance(in_path)

    # Read input
    with open(in_path, 'r') as f:
        in_data = json.load(f)

    # For step 1, in_data has a "values" key; for other steps, in_data has a "data" key
    if step == 1:
        # Step 1 reads the raw input.json
        input_data = in_data
    else:
        # Steps 2-18 read the output of the previous step
        input_data = in_data["data"]

    # Apply the step function
    func = STEP_FUNCTIONS[step]
    result = func(input_data)

    # Write output
    out_obj = {
        "step": step,
        "data": result,
        "provenance": provenance
    }

    with open(out_path, 'w') as f:
        json.dump(out_obj, f)


if __name__ == "__main__":
    main()
