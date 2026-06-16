"""
Signal processing pipeline with 10 steps.
CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json


def parse_float(data):
    """Step 1: Cast each element to float."""
    return [float(v) for v in data]


def normalize_minmax(data):
    """Step 2: Min-max normalization."""
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def scale(data):
    """Step 3: Multiply each element by 100."""
    return [v * 100 for v in data]


def round3(data):
    """Step 4: Round each element to 3 decimal places."""
    return [round(v, 3) for v in data]


def moving_avg_3(data):
    """Step 5: Sliding window mean of width 3."""
    result = []
    for i in range(len(data) - 2):
        result.append((data[i] + data[i + 1] + data[i + 2]) / 3)
    return result


def square(data):
    """Step 6: Square each element."""
    return [v * v for v in data]


def prefix_max(data):
    """Step 7: Running maximum."""
    result = []
    current_max = None
    for v in data:
        if current_max is None or v > current_max:
            current_max = v
        result.append(current_max)
    return result


def diffs(data):
    """Step 8: Consecutive differences."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def sort_desc(data):
    """Step 9: Sort descending."""
    return sorted(data, reverse=True)


def aggregate(data):
    """Step 10: Summary stats dict."""
    return {
        "sum": float(sum(data)),
        "mean": float(sum(data) / len(data)),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": int(len(data)),
    }


STEP_FUNCTIONS = {
    1: ("values", parse_float),
    2: ("data", normalize_minmax),
    3: ("data", scale),
    4: ("data", round3),
    5: ("data", moving_avg_3),
    6: ("data", square),
    7: ("data", prefix_max),
    8: ("data", diffs),
    9: ("data", sort_desc),
    10: ("data", aggregate),
}


def main():
    parser = argparse.ArgumentParser(description="Signal chain pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-10)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    # Read input file bytes for provenance
    with open(args.in_path, "rb") as f:
        in_bytes = f.read()

    provenance = hashlib.sha256(in_bytes).hexdigest()

    # Parse input JSON
    in_data = json.loads(in_bytes.decode("utf-8"))

    step_num = args.step
    if step_num not in STEP_FUNCTIONS:
        raise ValueError(f"Unknown step: {step_num}")

    input_key, step_fn = STEP_FUNCTIONS[step_num]
    input_values = in_data[input_key]

    result = step_fn(input_values)

    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
