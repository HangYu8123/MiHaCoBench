"""
vector_forge — 6-step vector-processing pipeline
Usage: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(prev):
    """Cast each element of values to float."""
    return [float(x) for x in prev["values"]]


def step2_double(prev):
    """Multiply each element by 2."""
    return [x * 2.0 for x in prev["data"]]


def step3_add_const(prev):
    """Add 3 to each element."""
    return [x + 3.0 for x in prev["data"]]


def step4_filter_gt_mean(prev):
    """Keep only elements strictly greater than the mean."""
    data = prev["data"]
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step5_sort_desc(prev):
    """Sort in descending order."""
    return sorted(prev["data"], reverse=True)


def step6_aggregate(prev):
    """Compute summary statistics."""
    data = prev["data"]
    count = len(data)
    total = sum(data)
    return {
        "sum": float(total),
        "mean": float(total / count),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": count,
    }


STEPS = {
    1: step1_parse,
    2: step2_double,
    3: step3_add_const,
    4: step4_filter_gt_mean,
    5: step5_sort_desc,
    6: step6_aggregate,
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

    if step not in STEPS:
        print(f"Unknown step: {step}", file=sys.stderr)
        sys.exit(1)

    provenance = compute_provenance(in_path)

    with open(in_path, "r") as f:
        prev = json.load(f)

    result = STEPS[step](prev)

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
