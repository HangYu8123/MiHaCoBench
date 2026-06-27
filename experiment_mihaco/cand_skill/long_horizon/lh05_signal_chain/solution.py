"""
10-step signal processing pipeline CLI.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step1_parse_float(input_data):
    """Cast each element of 'values' to float."""
    return [float(v) for v in input_data["values"]]


def step2_normalize_minmax(input_data):
    """Min-max normalize each element; all-zeros if max == min."""
    d = input_data["data"]
    mn = min(d)
    mx = max(d)
    if mx == mn:
        return [0.0 for _ in d]
    return [(v - mn) / (mx - mn) for v in d]


def step3_scale(input_data):
    """Multiply each element by 100."""
    d = input_data["data"]
    return [v * 100.0 for v in d]


def step4_round3(input_data):
    """Round each element to 3 decimal places."""
    d = input_data["data"]
    return [round(v, 3) for v in d]


def step5_moving_avg_3(input_data):
    """Sliding window mean of width 3."""
    d = input_data["data"]
    return [(d[i] + d[i + 1] + d[i + 2]) / 3.0 for i in range(len(d) - 2)]


def step6_square(input_data):
    """Square each element."""
    d = input_data["data"]
    return [v * v for v in d]


def step7_prefix_max(input_data):
    """Running maximum: result[i] = max(data[0..i])."""
    d = input_data["data"]
    if not d:
        return []
    cur = d[0]
    result = [cur]
    for v in d[1:]:
        cur = max(cur, v)
        result.append(cur)
    return result


def step8_diffs(input_data):
    """Consecutive differences: result[i] = data[i+1] - data[i]."""
    d = input_data["data"]
    return [d[i + 1] - d[i] for i in range(len(d) - 1)]


def step9_sort_desc(input_data):
    """Sort descending."""
    d = input_data["data"]
    return sorted(d, reverse=True)


def step10_aggregate(input_data):
    """Summary stats dict."""
    d = input_data["data"]
    return {
        "sum": sum(d),
        "mean": sum(d) / len(d),
        "min": min(d),
        "max": max(d),
        "count": len(d),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

STEPS = {
    1: step1_parse_float,
    2: step2_normalize_minmax,
    3: step3_scale,
    4: step4_round3,
    5: step5_moving_avg_3,
    6: step6_square,
    7: step7_prefix_max,
    8: step8_diffs,
    9: step9_sort_desc,
    10: step10_aggregate,
}


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Signal processing pipeline step runner.")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-10).")
    # --in is a reserved keyword in Python; use dest='in_path' to avoid SyntaxError
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path.")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path.")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_num not in STEPS:
        print(f"Error: step must be 1-10, got {step_num}", file=sys.stderr)
        sys.exit(1)

    # --- Provenance: compute SHA-256 of raw input bytes BEFORE any parsing ---
    with open(in_path, "rb") as f:
        raw_bytes = f.read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # --- Parse input JSON ---
    input_data = json.loads(raw_bytes)

    # --- Run the step ---
    result = STEPS[step_num](input_data)

    # --- Write output ---
    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }
    with open(out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
