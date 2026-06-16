"""
vector_forge — 6-step vector-processing pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json


def compute_provenance(in_path: str) -> str:
    """Compute SHA-256 of the exact bytes of the input file."""
    raw = open(in_path, 'rb').read()
    return hashlib.sha256(raw).hexdigest()


def step1_parse(data):
    """Cast each element of 'values' to float."""
    return [float(x) for x in data]


def step2_double(data):
    """Multiply each element by 2."""
    return [x * 2 for x in data]


def step3_add_const(data):
    """Add 3 to each element."""
    return [x + 3 for x in data]


def step4_filter_gt_mean(data):
    """Compute mean of full list; keep only elements strictly greater than mean."""
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step5_sort_desc(data):
    """Sort list in descending order."""
    return sorted(data, reverse=True)


def step6_aggregate(data):
    """Compute summary statistics over the list."""
    total = sum(data)
    count = len(data)
    return {
        "sum": float(total),
        "mean": float(total / count),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": int(count),
    }


def main():
    parser = argparse.ArgumentParser(description="vector_forge pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-6)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes first for provenance hash, then parse JSON
    raw = open(args.in_path, 'rb').read()
    provenance = hashlib.sha256(raw).hexdigest()
    prev = json.loads(raw)

    step = args.step

    if step == 1:
        # Step 1 reads "values" key from the original input
        result = step1_parse(prev["values"])
    elif step == 2:
        result = step2_double(prev["data"])
    elif step == 3:
        result = step3_add_const(prev["data"])
    elif step == 4:
        result = step4_filter_gt_mean(prev["data"])
    elif step == 5:
        result = step5_sort_desc(prev["data"])
    elif step == 6:
        result = step6_aggregate(prev["data"])
    else:
        raise ValueError(f"Unknown step: {step}")

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, 'w') as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
