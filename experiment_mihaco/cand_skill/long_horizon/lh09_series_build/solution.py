"""
18-step numeric pipeline: series_build (lh09)

CLI contract:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Step 1 reads data/input.json with key "values".
Steps 2-18 read the prior step's output JSON with key "data".
"""

import argparse
import hashlib
import itertools
import json


def read_input(step: int, path: str):
    """Read input JSON and return the relevant data field."""
    with open(path, 'r') as f:
        parsed = json.load(f)
    if step == 1:
        return parsed["values"]
    else:
        return parsed["data"]


def write_output(step: int, data, in_path: str, out_path: str) -> None:
    """Write output JSON with step, data, and provenance."""
    with open(in_path, 'rb') as f:
        raw_bytes = f.read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    result = {
        "step": step,
        "data": data,
        "provenance": provenance,
    }
    with open(out_path, 'w') as f:
        json.dump(result, f)


def step_1_parse_float(data):
    """Cast every integer in values to float."""
    return [float(v) for v in data]


def step_2_double(lst):
    """Multiply every element by 2."""
    return [v * 2 for v in lst]


def step_3_add_const(lst):
    """Add 2 to every element."""
    return [v + 2 for v in lst]


def step_4_cumsum(lst):
    """Replace with running cumulative sum (left to right)."""
    return list(itertools.accumulate(lst))


def step_5_mod(lst):
    """Replace every element with v % 13 (Python modulo)."""
    return [v % 13 for v in lst]


def step_6_scale_by_index(lst):
    """Multiply every element by its 0-based index: v[i] *= i."""
    return [v * i for i, v in enumerate(lst)]


def step_7_prefix_max(lst):
    """Replace with running prefix maximum (left to right)."""
    return list(itertools.accumulate(lst, max))


def step_8_diffs(lst):
    """Replace with consecutive differences: [s[1]-s[0], s[2]-s[1], ...]."""
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


def step_9_abs(lst):
    """Take the absolute value of every element."""
    return [abs(v) for v in lst]


def step_10_filter_gt_mean(lst):
    """Keep only elements strictly greater than the mean."""
    mean = sum(lst) / len(lst)
    return [v for v in lst if v > mean]


def step_11_square(lst):
    """Square every element (v**2)."""
    return [v ** 2 for v in lst]


def step_12_normalize_minmax(lst):
    """Min-max normalize to [0, 1]. If all equal, output all zeros."""
    lo = min(lst)
    hi = max(lst)
    if hi == lo:
        return [0.0] * len(lst)
    return [(v - lo) / (hi - lo) for v in lst]


def step_13_scale(lst):
    """Multiply every element by 100."""
    return [v * 100 for v in lst]


def step_14_round3(lst):
    """Round every element to 3 decimal places."""
    return [round(v, 3) for v in lst]


def step_15_moving_avg_3(lst):
    """3-element moving average. Indices 0,1 pass through unchanged."""
    result = []
    for i, v in enumerate(lst):
        if i < 2:
            result.append(v)
        else:
            result.append((lst[i - 2] + lst[i - 1] + lst[i]) / 3)
    return result


def step_16_sort_desc(lst):
    """Sort the list in descending order."""
    return sorted(lst, reverse=True)


def step_17_top_k(lst):
    """Keep only the first 6 elements; if fewer than 6, keep all."""
    return lst[:6]


def step_18_aggregate(lst):
    """Compute aggregate statistics over the list."""
    n = len(lst)
    s = sum(lst)
    return {
        "sum": float(s),
        "mean": float(s / n),
        "count": int(n),
        "min": float(min(lst)),
        "max": float(max(lst)),
    }


STEP_FUNCTIONS = {
    1: step_1_parse_float,
    2: step_2_double,
    3: step_3_add_const,
    4: step_4_cumsum,
    5: step_5_mod,
    6: step_6_scale_by_index,
    7: step_7_prefix_max,
    8: step_8_diffs,
    9: step_9_abs,
    10: step_10_filter_gt_mean,
    11: step_11_square,
    12: step_12_normalize_minmax,
    13: step_13_scale,
    14: step_14_round3,
    15: step_15_moving_avg_3,
    16: step_16_sort_desc,
    17: step_17_top_k,
    18: step_18_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="18-step numeric pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-18)")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="output", required=True, help="Output JSON path")
    args = parser.parse_args()

    step = args.step
    in_path = args.input
    out_path = args.output

    if step not in STEP_FUNCTIONS:
        raise ValueError(f"Invalid step: {step}. Must be 1-18.")

    data = read_input(step, in_path)
    result = STEP_FUNCTIONS[step](data)
    write_output(step, result, in_path, out_path)


if __name__ == "__main__":
    main()
