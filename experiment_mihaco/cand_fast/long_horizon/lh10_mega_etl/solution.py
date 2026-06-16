#!/usr/bin/env python3
"""
Mega ETL pipeline — 20-step chain.
Usage: python solution.py --step <K> --in <input_json> --out <output_json>
"""

import argparse
import hashlib
import json
import itertools
import sys


def compute_provenance(in_path: str) -> str:
    """SHA256 of exact bytes of the input file."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(data):
    """Read 'values' key; convert each to float."""
    return [float(x) for x in data["values"]]


def step2_add_const(data):
    """Add 7.0 to every element."""
    return [x + 7.0 for x in data]


def step3_double(data):
    """Multiply every element by 2."""
    return [x * 2.0 for x in data]


def step4_mod(data):
    """Apply modulo 11 to every element (floating-point %)."""
    return [x % 11.0 for x in data]


def step5_scale_by_index(data):
    """Multiply each element by its 1-based position."""
    return [v * (i + 1) for i, v in enumerate(data)]


def step6_cumsum(data):
    """Running cumulative sum."""
    result = []
    running = 0.0
    for x in data:
        running += x
        result.append(running)
    return result


def step7_prefix_max(data):
    """Running maximum from left."""
    result = []
    running_max = None
    for x in data:
        if running_max is None or x > running_max:
            running_max = x
        result.append(running_max)
    return result


def step8_prefix_min(data):
    """Running minimum from right: result[i] = min(data[i..end])."""
    n = len(data)
    result = [0.0] * n
    running_min = None
    for i in range(n - 1, -1, -1):
        if running_min is None or data[i] < running_min:
            running_min = data[i]
        result[i] = running_min
    return result


def step9_diffs(data):
    """Consecutive differences: result[i] = data[i+1] - data[i]."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step10_abs(data):
    """Absolute value of every element."""
    return [abs(x) for x in data]


def step11_square(data):
    """Square every element."""
    return [x * x for x in data]


def step12_normalize_minmax(data):
    """Min-max normalization to [0, 1]."""
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(x - mn) / (mx - mn) for x in data]


def step13_scale(data):
    """Multiply every element by 1000."""
    return [x * 1000.0 for x in data]


def step14_round3(data):
    """Round every element to 3 decimal places."""
    return [round(x, 3) for x in data]


def step15_moving_avg_3(data):
    """Trailing 3-element moving average with boundary handling."""
    n = len(data)
    result = []
    for k in range(n):
        if k == 0:
            result.append(data[0])
        elif k == 1:
            result.append((data[0] + data[1]) / 2.0)
        else:
            result.append((data[k - 2] + data[k - 1] + data[k]) / 3.0)
    return result


def step16_filter_gt_mean(data):
    """Keep only elements strictly greater than the arithmetic mean."""
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step17_sort_desc(data):
    """Sort in descending order."""
    return sorted(data, reverse=True)


def step18_dedupe(data):
    """Remove duplicate values, keeping first occurrence in current order."""
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step19_top_k(data):
    """Keep the first 5 elements (list already sorted descending)."""
    return data[:5]


def step20_aggregate(data):
    """Compute summary statistics over the 5 values."""
    total = sum(data)
    return {
        "sum": float(total),
        "mean": float(total / len(data)),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": 5,
    }


STEP_FUNCS = {
    1: step1_parse,
    2: step2_add_const,
    3: step3_double,
    4: step4_mod,
    5: step5_scale_by_index,
    6: step6_cumsum,
    7: step7_prefix_max,
    8: step8_prefix_min,
    9: step9_diffs,
    10: step10_abs,
    11: step11_square,
    12: step12_normalize_minmax,
    13: step13_scale,
    14: step14_round3,
    15: step15_moving_avg_3,
    16: step16_filter_gt_mean,
    17: step17_sort_desc,
    18: step18_dedupe,
    19: step19_top_k,
    20: step20_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="Mega ETL pipeline step executor")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-20)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Compute provenance BEFORE reading/parsing
    provenance = compute_provenance(in_path)

    # Read and parse input
    with open(in_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    # Step 1 reads 'values' key directly from payload
    # Steps 2-20 read 'data' key from payload
    if step == 1:
        input_data = payload
    else:
        input_data = payload["data"]

    if step not in STEP_FUNCS:
        print(f"Unknown step: {step}", file=sys.stderr)
        sys.exit(1)

    result = STEP_FUNCS[step](input_data)

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    output_str = json.dumps(output)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output_str)


if __name__ == "__main__":
    main()
