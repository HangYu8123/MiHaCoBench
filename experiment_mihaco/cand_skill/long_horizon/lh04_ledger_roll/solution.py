"""
lh04_ledger_roll — 8-step ledger pipeline.

CLI contract:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Each step reads the JSON at --in, computes its result, and writes to --out:
    {"step": K, "data": <result>, "provenance": "<sha256 hex of --in file bytes>"}
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    """Return sha256 hex digest of the raw bytes of in_path."""
    with open(in_path, "rb") as f:
        raw = f.read()
    return hashlib.sha256(raw).hexdigest()


def write_out(out_path: str, step_k: int, data, provenance: str) -> None:
    """Write the output artifact JSON with exactly the required keys."""
    artifact = {
        "step": step_k,
        "data": data,
        "provenance": provenance,
    }
    with open(out_path, "w") as f:
        json.dump(artifact, f)


def step1_parse(input_data: dict):
    """Cast every element of 'values' to float."""
    values = input_data["values"]
    return [float(x) for x in values]


def step2_cumsum(data: list) -> list:
    """Running cumulative sum."""
    result = []
    running = 0.0
    for x in data:
        running += x
        result.append(running)
    return result


def step3_prefix_min(data: list) -> list:
    """Running minimum (min seen so far at each index)."""
    result = []
    running_min = data[0]
    result.append(running_min)
    for x in data[1:]:
        running_min = min(running_min, x)
        result.append(running_min)
    return result


def step4_diffs(data: list) -> list:
    """Consecutive differences: data[i+1] - data[i]."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step5_abs(data: list) -> list:
    """Element-wise absolute value."""
    return [abs(x) for x in data]


def step6_sort_asc(data: list) -> list:
    """Sort in ascending order."""
    return sorted(data)


def step7_dedupe(data: list) -> list:
    """Remove duplicates, preserving order from step 6 (keep first occurrence)."""
    seen = set()
    out = []
    for x in data:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def step8_aggregate(data: list) -> dict:
    """Compute sum, mean, count, min, max over step 7's list."""
    total = float(sum(data))
    count = int(len(data))
    mean = float(total / count)
    minimum = float(min(data))
    maximum = float(max(data))
    return {
        "sum": total,
        "mean": mean,
        "count": count,
        "min": minimum,
        "max": maximum,
    }


STEP_FUNCS = {
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

    step_k = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_k not in STEP_FUNCS:
        print(f"Error: --step must be 1-8, got {step_k}", file=sys.stderr)
        sys.exit(1)

    # Compute provenance from raw bytes BEFORE parsing
    provenance = compute_provenance(in_path)

    # Load input JSON
    with open(in_path, "r") as f:
        input_json = json.load(f)

    # Step 1 reads "values"; steps 2-8 read "data"
    if step_k == 1:
        input_data = input_json
    else:
        input_data = input_json["data"]

    # Execute the step function
    result = STEP_FUNCS[step_k](input_data)

    # Write output artifact
    write_out(out_path, step_k, result, provenance)


if __name__ == "__main__":
    main()
