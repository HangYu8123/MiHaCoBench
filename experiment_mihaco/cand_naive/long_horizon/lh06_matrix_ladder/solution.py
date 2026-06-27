"""
matrix_ladder — 12-step pipeline solution.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json


def compute_provenance(in_path: str) -> str:
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(data):
    """Convert each integer in values to float."""
    return [float(x) for x in data["values"]]


def step2_add_const(data):
    """Add 5.0 to every element."""
    return [x + 5.0 for x in data]


def step3_mod(data):
    """Apply % 7 to every element (Python float %)."""
    return [x % 7 for x in data]


def step4_scale_by_index(data):
    """Multiply element at position i by i (0-based)."""
    return [float(i) * x for i, x in enumerate(data)]


def step5_cumsum(data):
    """Running cumulative sum left-to-right."""
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step6_prefix_max(data):
    """Running maximum left-to-right."""
    result = []
    current_max = None
    for x in data:
        if current_max is None or x > current_max:
            current_max = x
        result.append(current_max)
    return result


def step7_diffs(data):
    """Consecutive differences: data[i+1] - data[i]."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step8_abs(data):
    """Absolute value of every element."""
    return [abs(x) for x in data]


def step9_filter_gt_mean(data):
    """Keep only elements strictly greater than the mean."""
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step10_sort_asc(data):
    """Sort elements ascending."""
    return sorted(data)


def step11_dedupe(data):
    """Remove duplicate values, preserving order of first occurrence."""
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step12_aggregate(data):
    """Compute summary statistics."""
    total = sum(data)
    count = len(data)
    mean = total / count
    return {
        "total": float(total),
        "mean": float(mean),
        "count": int(count),
        "min": float(min(data)),
        "max": float(max(data)),
    }


STEPS = {
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
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Compute provenance from the exact bytes of the input file
    provenance = compute_provenance(in_path)

    # Read input JSON
    with open(in_path, "r", encoding="utf-8") as f:
        in_data = json.load(f)

    # Step 1 reads raw input with key "values"
    # Steps 2-12 read from "data" key of the previous step's output
    if step_num == 1:
        input_for_step = in_data
    else:
        input_for_step = in_data["data"]

    # Execute the step
    step_fn = STEPS[step_num]
    result = step_fn(input_for_step)

    # Write output
    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
