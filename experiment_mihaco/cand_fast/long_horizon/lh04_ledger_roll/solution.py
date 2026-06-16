"""
lh04_ledger_roll — 8-step ledger pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the raw bytes of the input file."""
    with open(in_path, "rb") as f:
        raw = f.read()
    return hashlib.sha256(raw).hexdigest()


def read_input(in_path: str, step: int):
    """Read JSON from in_path and return the appropriate data payload."""
    with open(in_path, "r") as f:
        obj = json.load(f)
    if step == 1:
        # Step 1 reads from data/input.json, key is "values"
        return obj["values"]
    else:
        # Steps 2-8 read from the previous step's artifact, key is "data"
        return obj["data"]


def write_output(out_path: str, step: int, data, provenance: str) -> None:
    """Write the output JSON with exactly keys: step, data, provenance."""
    out_obj = {
        "step": int(step),
        "data": data,
        "provenance": provenance,
    }
    with open(out_path, "w") as f:
        json.dump(out_obj, f)


def step1_parse(data):
    """Cast every element of values to float."""
    return [float(x) for x in data]


def step2_cumsum(data):
    """Running cumulative sum."""
    result = []
    running = 0.0
    for x in data:
        running += float(x)
        result.append(running)
    return result


def step3_prefix_min(data):
    """Running minimum (min seen so far at each index)."""
    result = []
    current_min = None
    for x in data:
        val = float(x)
        if current_min is None or val < current_min:
            current_min = val
        result.append(current_min)
    return result


def step4_diffs(data):
    """Consecutive differences: data[i+1] - data[i] for i in 0..len-2."""
    n = len(data)
    return [float(data[i + 1]) - float(data[i]) for i in range(n - 1)]


def step5_abs(data):
    """Element-wise absolute value."""
    return [float(abs(float(x))) for x in data]


def step6_sort_asc(data):
    """Sort in ascending order."""
    return sorted([float(x) for x in data])


def step7_dedupe(data):
    """Remove duplicates, preserving first-occurrence order."""
    seen = set()
    result = []
    for x in data:
        val = float(x)
        if val not in seen:
            seen.add(val)
            result.append(val)
    return result


def step8_aggregate(data):
    """Compute sum, mean, count, min, max over the list."""
    floats = [float(x) for x in data]
    count = int(len(floats))
    total = float(sum(floats))
    mean = float(total / count) if count > 0 else float("nan")
    mn = float(min(floats))
    mx = float(max(floats))
    return {
        "sum": total,
        "mean": mean,
        "count": count,
        "min": mn,
        "max": mx,
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
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Compute provenance on raw bytes BEFORE parsing
    provenance = compute_provenance(in_path)

    # Read input data
    raw_data = read_input(in_path, step)

    # Dispatch to the appropriate step function
    if step not in STEP_FUNCTIONS:
        raise ValueError(f"Unknown step: {step}. Must be 1-8.")

    result = STEP_FUNCTIONS[step](raw_data)

    # Write output
    write_output(out_path, step, result, provenance)


if __name__ == "__main__":
    main()
