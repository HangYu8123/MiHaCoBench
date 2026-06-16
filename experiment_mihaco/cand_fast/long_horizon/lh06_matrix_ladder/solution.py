"""
Long-Horizon 06 — matrix_ladder (12 steps)

CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import itertools
import json


def compute_provenance(in_path: str) -> str:
    """Compute SHA-256 hex digest of the raw bytes of the input file."""
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def step1_parse(data: dict) -> list:
    """Convert each integer in 'values' to float."""
    return [float(x) for x in data["values"]]


def step2_add_const(data: list) -> list:
    """Add 5.0 to every element."""
    return [x + 5.0 for x in data]


def step3_mod(data: list) -> list:
    """Apply % 7 to every element (Python float %)."""
    return [x % 7 for x in data]


def step4_scale_by_index(data: list) -> list:
    """Multiply element at position i by i (0-based)."""
    return [float(i * x) for i, x in enumerate(data)]


def step5_cumsum(data: list) -> list:
    """Running cumulative sum left-to-right."""
    return [float(x) for x in itertools.accumulate(data)]


def step6_prefix_max(data: list) -> list:
    """Running maximum left-to-right."""
    return [float(x) for x in itertools.accumulate(data, max)]


def step7_diffs(data: list) -> list:
    """Consecutive differences: data[i+1] - data[i]. Length n-1."""
    return [float(data[i + 1] - data[i]) for i in range(len(data) - 1)]


def step8_abs(data: list) -> list:
    """Absolute value of every element."""
    return [float(abs(x)) for x in data]


def step9_filter_gt_mean(data: list) -> list:
    """Keep only elements strictly greater than the mean."""
    mean = sum(data) / len(data)
    return [float(x) for x in data if x > mean]


def step10_sort_asc(data: list) -> list:
    """Sort elements ascending."""
    return [float(x) for x in sorted(data)]


def step11_dedupe(data: list) -> list:
    """Remove duplicate values, preserving order of first occurrence."""
    return [float(x) for x in dict.fromkeys(data)]


def step12_aggregate(data: list) -> dict:
    """Compute summary statistics."""
    total = float(sum(data))
    count = int(len(data))
    mean = float(total / count)
    minimum = float(min(data))
    maximum = float(max(data))
    return {
        "total": total,
        "mean": mean,
        "count": count,
        "min": minimum,
        "max": maximum,
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
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    # Compute provenance from raw bytes BEFORE parsing
    provenance = compute_provenance(args.in_path)

    # Read and parse input JSON
    with open(args.in_path, "r") as f:
        input_json = json.load(f)

    # Step 1 reads "values" key; all other steps read "data" key
    if args.step == 1:
        input_data = input_json
    else:
        input_data = input_json["data"]

    # Apply the step function
    step_fn = STEP_FUNCTIONS[args.step]
    result = step_fn(input_data)

    # Write output JSON
    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
