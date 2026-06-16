"""
stats_cascade — 14-step numerical pipeline
Each invocation: python solution.py --step K --in <input_json> --out <output_json>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    """SHA-256 hex digest of the raw bytes of the input file."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step_1_parse(data):
    """Cast each element of input['values'] to float."""
    return [float(x) for x in data["values"]]


def step_2_double(data):
    """Multiply every element by 2."""
    return [x * 2.0 for x in data]


def step_3_square(data):
    """Raise every element to the power of 2."""
    return [x * x for x in data]


def step_4_normalize_minmax(data):
    """Apply min-max normalization: (x - min) / (max - min)."""
    mn = min(data)
    mx = max(data)
    denom = mx - mn
    return [(x - mn) / denom for x in data]


def step_5_scale(data):
    """Multiply every element by 50."""
    return [x * 50.0 for x in data]


def step_6_round3(data):
    """Round every element to 3 decimal places."""
    return [round(x, 3) for x in data]


def step_7_moving_avg_3(data):
    """Apply a 3-element moving average with edge handling."""
    result = []
    for i in range(len(data)):
        if i == 0:
            window = [data[0]]
        elif i == 1:
            window = [data[0], data[1]]
        else:
            window = [data[i - 2], data[i - 1], data[i]]
        result.append(sum(window) / len(window))
    return result


def step_8_cumsum(data):
    """Compute the running cumulative sum."""
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step_9_diffs(data):
    """Compute consecutive differences: out[i] = data[i+1] - data[i]."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_10_prefix_min(data):
    """Compute running prefix minimum."""
    result = []
    current_min = None
    for x in data:
        if current_min is None or x < current_min:
            current_min = x
        result.append(current_min)
    return result


def step_11_abs(data):
    """Take the absolute value of every element."""
    return [abs(x) for x in data]


def step_12_sort_desc(data):
    """Sort the list in descending order."""
    return sorted(data, reverse=True)


def step_13_top_k(data):
    """Keep only the first 8 elements."""
    return data[:8]


def step_14_aggregate(data):
    """Compute summary statistics over the 8-element list."""
    return {
        "sum": float(sum(data)),
        "mean": float(sum(data) / len(data)),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": int(len(data)),
    }


STEP_FUNCTIONS = {
    1: step_1_parse,
    2: step_2_double,
    3: step_3_square,
    4: step_4_normalize_minmax,
    5: step_5_scale,
    6: step_6_round3,
    7: step_7_moving_avg_3,
    8: step_8_cumsum,
    9: step_9_diffs,
    10: step_10_prefix_min,
    11: step_11_abs,
    12: step_12_sort_desc,
    13: step_13_top_k,
    14: step_14_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="stats_cascade pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-14)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step not in STEP_FUNCTIONS:
        print(f"Error: step must be between 1 and 14, got {step}", file=sys.stderr)
        sys.exit(1)

    # Compute provenance before reading data
    provenance = compute_provenance(in_path)

    # Read input
    with open(in_path, "r") as f:
        in_data = json.load(f)

    # Extract data field (step 1 reads the raw input, others read the 'data' field)
    if step == 1:
        input_data = in_data
    else:
        input_data = in_data["data"]

    # Apply the step function
    result = STEP_FUNCTIONS[step](input_data)

    # Write output
    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
