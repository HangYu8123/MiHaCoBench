"""
lh04_ledger_roll — 8-step ledger pipeline
Usage: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the exact bytes of the input file."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(data):
    """Cast every element of 'values' to float."""
    return [float(v) for v in data["values"]]


def step2_cumsum(data):
    """Running cumulative sum of the input list."""
    lst = data["data"]
    result = []
    total = 0.0
    for v in lst:
        total += float(v)
        result.append(total)
    return result


def step3_prefix_min(data):
    """Running minimum (min seen so far at each index)."""
    lst = data["data"]
    result = []
    current_min = None
    for v in lst:
        v = float(v)
        if current_min is None or v < current_min:
            current_min = v
        result.append(current_min)
    return result


def step4_diffs(data):
    """Consecutive differences: data[i+1] - data[i] for i in 0..len-2."""
    lst = [float(v) for v in data["data"]]
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


def step5_abs(data):
    """Element-wise absolute value."""
    return [abs(float(v)) for v in data["data"]]


def step6_sort_asc(data):
    """Sort in ascending order."""
    return sorted([float(v) for v in data["data"]])


def step7_dedupe(data):
    """Remove duplicate values, preserving order (keep first occurrence)."""
    lst = [float(v) for v in data["data"]]
    seen = set()
    result = []
    for v in lst:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def step8_aggregate(data):
    """Compute sum, mean, count, min, max over the list."""
    lst = [float(v) for v in data["data"]]
    count = len(lst)
    total = sum(lst)
    return {
        "sum": float(total),
        "mean": float(total / count) if count > 0 else 0.0,
        "count": count,
        "min": float(min(lst)),
        "max": float(max(lst)),
    }


STEP_FUNCTIONS = {
    1: step1_parse,
    2: step2_cumsum,
    3: step3_prefix_min,
    4: step4_diffs,
    5: step5_abs,
    6: step6_sort_asc,
    7: step7_dedupe,
    8: step8_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="lh04_ledger_roll pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-8)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_num not in STEP_FUNCTIONS:
        print(f"Error: step must be 1-8, got {step_num}", file=sys.stderr)
        sys.exit(1)

    # Read provenance from the exact bytes of the input file
    provenance = compute_provenance(in_path)

    # Read input JSON
    with open(in_path, "r", encoding="utf-8") as f:
        in_data = json.load(f)

    # Run the step function
    result = STEP_FUNCTIONS[step_num](in_data)

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
