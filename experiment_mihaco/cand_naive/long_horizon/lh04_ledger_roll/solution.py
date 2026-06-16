"""
lh04_ledger_roll — 8-step pipeline solution.

CLI usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import math
import sys


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the exact bytes of the input file."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(in_path: str) -> list:
    """Step 1: Cast every element of 'values' to float."""
    with open(in_path, 'r') as f:
        data = json.load(f)
    values = data["values"]
    return [float(v) for v in values]


def step2_cumsum(in_path: str) -> list:
    """Step 2: Running cumulative sum of step 1's list."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    result = []
    total = 0.0
    for v in values:
        total += v
        result.append(total)
    return result


def step3_prefix_min(in_path: str) -> list:
    """Step 3: Running minimum (min seen so far at each index) of step 2's list."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    result = []
    current_min = None
    for v in values:
        if current_min is None or v < current_min:
            current_min = v
        result.append(current_min)
    return result


def step4_diffs(in_path: str) -> list:
    """Step 4: Consecutive differences: data[i+1] - data[i] for i in 0..len-2."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    result = []
    for i in range(len(values) - 1):
        result.append(values[i + 1] - values[i])
    return result


def step5_abs(in_path: str) -> list:
    """Step 5: Element-wise absolute value of step 4's list."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    return [abs(v) for v in values]


def step6_sort_asc(in_path: str) -> list:
    """Step 6: Sort step 5's list in ascending order."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    return sorted(values)


def step7_dedupe(in_path: str) -> list:
    """Step 7: Remove duplicate values, preserving order from step 6 (keep first occurrence)."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    seen = set()
    result = []
    for v in values:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def step8_aggregate(in_path: str) -> dict:
    """Step 8: Compute sum, mean, count, min, max over step 7's list."""
    with open(in_path, 'r') as f:
        artifact = json.load(f)
    values = artifact["data"]
    count = len(values)
    total = sum(values)
    mean = total / count if count > 0 else 0.0
    return {
        "sum": float(total),
        "mean": float(mean),
        "count": int(count),
        "min": float(min(values)),
        "max": float(max(values)),
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
    parser.add_argument("--in", dest="in_path", required=True, help="Path to input JSON file")
    parser.add_argument("--out", dest="out_path", required=True, help="Path to output JSON file")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_num not in STEP_FUNCTIONS:
        print(f"Error: step must be between 1 and 8, got {step_num}", file=sys.stderr)
        sys.exit(1)

    # Compute provenance BEFORE reading data (same file bytes)
    provenance = compute_provenance(in_path)

    # Execute the step
    step_fn = STEP_FUNCTIONS[step_num]
    result = step_fn(in_path)

    # Write output artifact
    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, 'w') as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
