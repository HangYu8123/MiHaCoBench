"""
signal_chain — 10-step signal processing pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def step_parse_float(data):
    """Step 1: Cast each element to float."""
    return [float(v) for v in data]


def step_normalize_minmax(data):
    """Step 2: (v - min) / (max - min); all zeros if max == min."""
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step_scale(data):
    """Step 3: Multiply each element by 100."""
    return [v * 100.0 for v in data]


def step_round3(data):
    """Step 4: Round each element to 3 decimal places."""
    return [round(v, 3) for v in data]


def step_moving_avg_3(data):
    """Step 5: Sliding window mean of width 3."""
    result = []
    for i in range(len(data) - 2):
        result.append((data[i] + data[i + 1] + data[i + 2]) / 3.0)
    return result


def step_square(data):
    """Step 6: Square each element."""
    return [v * v for v in data]


def step_prefix_max(data):
    """Step 7: Running maximum."""
    result = []
    current_max = None
    for v in data:
        if current_max is None or v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step_diffs(data):
    """Step 8: Consecutive differences."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_sort_desc(data):
    """Step 9: Sort descending."""
    return sorted(data, reverse=True)


def step_aggregate(data):
    """Step 10: Summary stats dict."""
    total = sum(data)
    count = len(data)
    mean = total / count if count > 0 else 0.0
    return {
        "sum": total,
        "mean": mean,
        "min": min(data),
        "max": max(data),
        "count": count,
    }


STEPS = {
    1: step_parse_float,
    2: step_normalize_minmax,
    3: step_scale,
    4: step_round3,
    5: step_moving_avg_3,
    6: step_square,
    7: step_prefix_max,
    8: step_diffs,
    9: step_sort_desc,
    10: step_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="Signal processing pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-10)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Read and hash the input file
    with open(in_path, "rb") as f:
        raw_bytes = f.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()
    input_obj = json.loads(raw_bytes)

    # Extract the input data
    if step_num == 1:
        # Step 1 reads from input.json which has a "values" key
        data = input_obj["values"]
    else:
        # Steps 2+ read from the previous step's output which has a "data" key
        data = input_obj["data"]

    # Apply the step function
    if step_num not in STEPS:
        print(f"Unknown step: {step_num}", file=sys.stderr)
        sys.exit(1)

    result = STEPS[step_num](data)

    # Write the output
    output_obj = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(output_obj, f)


if __name__ == "__main__":
    main()
