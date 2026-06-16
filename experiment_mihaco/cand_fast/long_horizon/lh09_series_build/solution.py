"""
Long-Horizon 09 — series_build (18 steps)
CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def step_parse_float(data):
    """Step 1: Cast every integer in 'values' to float."""
    return [float(v) for v in data["values"]]


def step_double(data):
    """Step 2: Multiply every element by 2."""
    lst = data["data"]
    return [v * 2 for v in lst]


def step_add_const(data):
    """Step 3: Add 2 to every element."""
    lst = data["data"]
    return [v + 2 for v in lst]


def step_cumsum(data):
    """Step 4: Replace with running cumulative sum (left to right)."""
    lst = data["data"]
    result = []
    running = 0.0
    for v in lst:
        running += v
        result.append(running)
    return result


def step_mod(data):
    """Step 5: Replace every element with v % 13 (Python modulo)."""
    lst = data["data"]
    return [v % 13 for v in lst]


def step_scale_by_index(data):
    """Step 6: Multiply every element by its 0-based index."""
    lst = data["data"]
    return [v * i for i, v in enumerate(lst)]


def step_prefix_max(data):
    """Step 7: Replace with running prefix maximum (left to right)."""
    lst = data["data"]
    result = []
    current_max = float('-inf')
    for v in lst:
        if v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step_diffs(data):
    """Step 8: Replace with consecutive differences. Length = N-1."""
    lst = data["data"]
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


def step_abs(data):
    """Step 9: Take absolute value of every element."""
    lst = data["data"]
    return [abs(v) for v in lst]


def step_filter_gt_mean(data):
    """Step 10: Keep only elements strictly greater than the mean."""
    lst = data["data"]
    mean = sum(lst) / len(lst)
    return [v for v in lst if v > mean]


def step_square(data):
    """Step 11: Square every element."""
    lst = data["data"]
    return [v ** 2 for v in lst]


def step_normalize_minmax(data):
    """Step 12: Min-max normalize to [0, 1]. If all equal, output zeros."""
    lst = data["data"]
    mn = min(lst)
    mx = max(lst)
    if mx == mn:
        return [0.0] * len(lst)
    return [(v - mn) / (mx - mn) for v in lst]


def step_scale(data):
    """Step 13: Multiply every element by 100."""
    lst = data["data"]
    return [v * 100 for v in lst]


def step_round3(data):
    """Step 14: Round every element to 3 decimal places."""
    lst = data["data"]
    return [round(v, 3) for v in lst]


def step_moving_avg_3(data):
    """Step 15: 3-element moving average.
    Indices 0 and 1: output original value unchanged.
    Index i >= 2: (v[i-2] + v[i-1] + v[i]) / 3.
    """
    lst = data["data"]
    result = []
    for i, v in enumerate(lst):
        if i < 2:
            result.append(v)
        else:
            result.append((lst[i - 2] + lst[i - 1] + lst[i]) / 3)
    return result


def step_sort_desc(data):
    """Step 16: Sort the list in descending order."""
    lst = data["data"]
    return sorted(lst, reverse=True)


def step_top_k(data):
    """Step 17: Keep only the first 6 elements (top-6 after descending sort).
    If fewer than 6 elements exist, keep all.
    """
    lst = data["data"]
    k = min(6, len(lst))
    return lst[:k]


def step_aggregate(data):
    """Step 18: Compute sum, mean, count, min, max over the list."""
    lst = data["data"]
    total = sum(lst)
    count = len(lst)
    return {
        "sum": float(total),
        "mean": float(total / count),
        "count": int(count),
        "min": float(min(lst)),
        "max": float(max(lst)),
    }


STEP_FUNCTIONS = {
    1: step_parse_float,
    2: step_double,
    3: step_add_const,
    4: step_cumsum,
    5: step_mod,
    6: step_scale_by_index,
    7: step_prefix_max,
    8: step_diffs,
    9: step_abs,
    10: step_filter_gt_mean,
    11: step_square,
    12: step_normalize_minmax,
    13: step_scale,
    14: step_round3,
    15: step_moving_avg_3,
    16: step_sort_desc,
    17: step_top_k,
    18: step_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="series_build pipeline step executor")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-18)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Read raw bytes for provenance BEFORE any parsing
    raw_bytes = open(in_path, 'rb').read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse the JSON
    data = json.loads(raw_bytes)

    if step not in STEP_FUNCTIONS:
        print(f"Error: unknown step {step}", file=sys.stderr)
        sys.exit(1)

    result = STEP_FUNCTIONS[step](data)

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, 'w') as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
