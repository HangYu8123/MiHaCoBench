"""
Long-Horizon 09 — series_build (18 steps)
CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import math
import sys


def compute_provenance(in_path: str) -> str:
    """Compute SHA-256 hex digest of the input file bytes."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse_float(data):
    """Cast every integer in values to float."""
    values = data["values"]
    return [float(v) for v in values]


def step2_double(data):
    """Multiply every element by 2."""
    values = data["data"]
    return [v * 2.0 for v in values]


def step3_add_const(data):
    """Add 2 to every element."""
    values = data["data"]
    return [v + 2.0 for v in values]


def step4_cumsum(data):
    """Replace with running cumulative sum (left to right)."""
    values = data["data"]
    result = []
    running = 0.0
    for v in values:
        running += v
        result.append(running)
    return result


def step5_mod(data):
    """Replace every element with v % 13 (Python modulo)."""
    values = data["data"]
    return [v % 13 for v in values]


def step6_scale_by_index(data):
    """Multiply every element by its 0-based index."""
    values = data["data"]
    return [v * i for i, v in enumerate(values)]


def step7_prefix_max(data):
    """Replace with running prefix maximum (left to right)."""
    values = data["data"]
    result = []
    current_max = None
    for v in values:
        if current_max is None or v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step8_diffs(data):
    """Replace with consecutive differences."""
    values = data["data"]
    result = []
    for i in range(1, len(values)):
        result.append(values[i] - values[i - 1])
    return result


def step9_abs(data):
    """Take the absolute value of every element."""
    values = data["data"]
    return [abs(v) for v in values]


def step10_filter_gt_mean(data):
    """Keep only elements strictly greater than the mean."""
    values = data["data"]
    if not values:
        return []
    mean = sum(values) / len(values)
    return [v for v in values if v > mean]


def step11_square(data):
    """Square every element."""
    values = data["data"]
    return [v ** 2 for v in values]


def step12_normalize_minmax(data):
    """Min-max normalize to [0, 1]. If all equal, output all zeros."""
    values = data["data"]
    if not values:
        return []
    mn = min(values)
    mx = max(values)
    if mx == mn:
        return [0.0] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def step13_scale(data):
    """Multiply every element by 100."""
    values = data["data"]
    return [v * 100.0 for v in values]


def step14_round3(data):
    """Round every element to 3 decimal places."""
    values = data["data"]
    return [round(v, 3) for v in values]


def step15_moving_avg_3(data):
    """3-element moving average. Indices 0 and 1 unchanged; i >= 2: (v[i-2]+v[i-1]+v[i])/3."""
    values = data["data"]
    result = []
    for i, v in enumerate(values):
        if i < 2:
            result.append(v)
        else:
            result.append((values[i - 2] + values[i - 1] + values[i]) / 3.0)
    return result


def step16_sort_desc(data):
    """Sort the list in descending order."""
    values = data["data"]
    return sorted(values, reverse=True)


def step17_top_k(data):
    """Keep only the first 6 elements (top-6 after descending sort)."""
    values = data["data"]
    return values[:6]


def step18_aggregate(data):
    """Compute sum, mean, count, min, max over the list."""
    values = data["data"]
    n = len(values)
    if n == 0:
        return {"sum": 0.0, "mean": 0.0, "count": 0, "min": 0.0, "max": 0.0}
    total = sum(values)
    return {
        "sum": total,
        "mean": total / n,
        "count": n,
        "min": min(values),
        "max": max(values),
    }


STEPS = {
    1: step1_parse_float,
    2: step2_double,
    3: step3_add_const,
    4: step4_cumsum,
    5: step5_mod,
    6: step6_scale_by_index,
    7: step7_prefix_max,
    8: step8_diffs,
    9: step9_abs,
    10: step10_filter_gt_mean,
    11: step11_square,
    12: step12_normalize_minmax,
    13: step13_scale,
    14: step14_round3,
    15: step15_moving_avg_3,
    16: step16_sort_desc,
    17: step17_top_k,
    18: step18_aggregate,
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

    # Compute provenance before reading JSON (reads raw bytes)
    provenance = compute_provenance(in_path)

    # Read input JSON
    with open(in_path, 'r') as f:
        in_data = json.load(f)

    # Compute result
    result = STEPS[step](in_data)

    # Write output
    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, 'w') as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
