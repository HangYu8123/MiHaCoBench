"""
solution.py — matrix_ladder 12-step pipeline

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import math


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the exact bytes of the input file."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(data):
    """Convert each integer in values to float."""
    return [float(x) for x in data["values"]]


def step2_add_const(data):
    """Add 5.0 to every element."""
    return [x + 5.0 for x in data["data"]]


def step3_mod(data):
    """Apply % 7 to every element (Python float %)."""
    return [x % 7 for x in data["data"]]


def step4_scale_by_index(data):
    """Multiply element at position i by i (0-based)."""
    return [float(i) * x for i, x in enumerate(data["data"])]


def step5_cumsum(data):
    """Running cumulative sum left-to-right."""
    result = []
    total = 0.0
    for x in data["data"]:
        total += x
        result.append(total)
    return result


def step6_prefix_max(data):
    """Running maximum left-to-right."""
    result = []
    current_max = -math.inf
    for x in data["data"]:
        if x > current_max:
            current_max = x
        result.append(current_max)
    return result


def step7_diffs(data):
    """Consecutive differences: data[i+1] - data[i]."""
    lst = data["data"]
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


def step8_abs(data):
    """Absolute value of every element."""
    return [abs(x) for x in data["data"]]


def step9_filter_gt_mean(data):
    """Keep only elements strictly greater than the mean of the list."""
    lst = data["data"]
    if not lst:
        return []
    mean = sum(lst) / len(lst)
    return [x for x in lst if x > mean]


def step10_sort_asc(data):
    """Sort elements ascending."""
    return sorted(data["data"])


def step11_dedupe(data):
    """Remove duplicate values, preserving order of first occurrence."""
    seen = set()
    result = []
    for x in data["data"]:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step12_aggregate(data):
    """Compute summary statistics."""
    lst = data["data"]
    total = sum(lst)
    count = len(lst)
    mean = total / count if count > 0 else 0.0
    minimum = min(lst) if lst else 0.0
    maximum = max(lst) if lst else 0.0
    return {
        "total": float(total),
        "mean": float(mean),
        "count": int(count),
        "min": float(minimum),
        "max": float(maximum),
    }


STEP_FUNCTIONS = {
    1: step1_parse,
    2: step2_add_const,
    3: step3_mod,
    4: step4_scale_by_index,
    5: step5_cumsum,
    6: step6_prefix_max,
    7: step7_diffs,
    8: step8_abs,
    9: step9_filter_gt_mean,
    10: step10_sort_asc,
    11: step11_dedupe,
    12: step12_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="matrix_ladder pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-12)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Compute provenance from the input file bytes
    provenance = compute_provenance(in_path)

    # Read the input data
    with open(in_path, "r") as f:
        input_data = json.load(f)

    # Run the appropriate step
    if step_num not in STEP_FUNCTIONS:
        raise ValueError(f"Unknown step: {step_num}")

    result = STEP_FUNCTIONS[step_num](input_data)

    # Write the output
    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
