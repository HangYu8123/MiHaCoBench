"""
solution.py — vector_forge pipeline (6 steps)

CLI:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Each step reads the JSON at --in, computes its result, and writes to --out:
    {"step": <K>, "data": <result>, "provenance": "<sha256 hex of --in file bytes>"}
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the exact bytes of the input file."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(prev: dict) -> list:
    """Cast each element of values to float (identity, no scaling)."""
    values = prev["values"]
    return [float(x) for x in values]


def step2_double(prev: dict) -> list:
    """Multiply each element by 2."""
    data = prev["data"]
    return [x * 2.0 for x in data]


def step3_add_const(prev: dict) -> list:
    """Add 3 to each element."""
    data = prev["data"]
    return [x + 3.0 for x in data]


def step4_filter_gt_mean(prev: dict) -> list:
    """Compute the mean; keep only elements strictly greater than the mean."""
    data = prev["data"]
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step5_sort_desc(prev: dict) -> list:
    """Sort the filtered list in descending order."""
    data = prev["data"]
    return sorted(data, reverse=True)


def step6_aggregate(prev: dict) -> dict:
    """Compute summary statistics over the sorted list."""
    data = prev["data"]
    count = len(data)
    total = sum(data)
    mean = total / count
    minimum = min(data)
    maximum = max(data)
    return {
        "sum": float(total),
        "mean": float(mean),
        "min": float(minimum),
        "max": float(maximum),
        "count": int(count),
    }


STEP_HANDLERS = {
    1: step1_parse,
    2: step2_double,
    3: step3_add_const,
    4: step4_filter_gt_mean,
    5: step5_sort_desc,
    6: step6_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="vector_forge pipeline step runner")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-6)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step not in STEP_HANDLERS:
        print(f"Error: step must be 1-6, got {step}", file=sys.stderr)
        sys.exit(1)

    # Compute provenance BEFORE reading JSON (same file bytes)
    provenance = compute_provenance(in_path)

    # Read the input JSON
    with open(in_path, "r", encoding="utf-8") as f:
        prev = json.load(f)

    # Run the step handler
    handler = STEP_HANDLERS[step]
    result = handler(prev)

    # Write the output JSON
    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Step {step} complete. Output written to {out_path}")


if __name__ == "__main__":
    main()
