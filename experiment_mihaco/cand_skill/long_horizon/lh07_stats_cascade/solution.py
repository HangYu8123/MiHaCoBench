"""
stats_cascade — 14-step numerical pipeline (single file).

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Step 1 reads data/input.json whose top-level key is "values".
Steps 2-14 read the previous step's output whose top-level key is "data".
"""

import argparse
import hashlib
import json
from itertools import accumulate


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step_parse(obj):
    """Step 1: read 'values' key; cast each element to float."""
    return [float(x) for x in obj["values"]]


def step_double(data):
    """Step 2: multiply every element by 2."""
    return [x * 2 for x in data]


def step_square(data):
    """Step 3: raise every element to the power of 2 (x * x)."""
    return [x * x for x in data]


def step_normalize_minmax(data):
    """Step 4: min-max normalization."""
    mn = min(data)
    mx = max(data)
    return [(x - mn) / (mx - mn) for x in data]


def step_scale(data):
    """Step 5: multiply every element by 50."""
    return [x * 50 for x in data]


def step_round3(data):
    """Step 6: round every element to 3 decimal places using stdlib round()."""
    return [round(x, 3) for x in data]


def step_moving_avg_3(data):
    """Step 7: 3-element moving average with asymmetric window.

    - i == 0: window = [data[0]]               (length 1)
    - i == 1: window = [data[0], data[1]]      (length 2)
    - i >= 2: window = [data[i-2], data[i-1], data[i]]  (length 3)
    """
    result = []
    for i in range(len(data)):
        if i == 0:
            window = [data[0]]
        elif i == 1:
            window = [data[0], data[1]]
        else:
            window = [data[i - 2], data[i - 1], data[i]]
        result.append(sum(window) / len(window))
    return result


def step_cumsum(data):
    """Step 8: running cumulative sum."""
    return list(accumulate(data))


def step_diffs(data):
    """Step 9: consecutive differences; output length = len(data) - 1 = 17."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_prefix_min(data):
    """Step 10: running prefix minimum."""
    result = []
    cur_min = data[0]
    for x in data:
        if x < cur_min:
            cur_min = x
        result.append(cur_min)
    return result


def step_abs(data):
    """Step 11: absolute value of every element."""
    return [abs(x) for x in data]


def step_sort_desc(data):
    """Step 12: sort in descending order."""
    return sorted(data, reverse=True)


def step_top_k(data):
    """Step 13: keep only the first 8 elements."""
    return data[:8]


def step_aggregate(data):
    """Step 14: summary statistics dict over the 8-element list."""
    total = sum(data)
    n = len(data)
    return {
        "sum": float(total),
        "mean": float(total) / n,
        "min": float(min(data)),
        "max": float(max(data)),
        "count": n,
    }


# ---------------------------------------------------------------------------
# Dispatch table — maps step number to (reads_values_key, function)
# ---------------------------------------------------------------------------

STEPS = {
    1:  (True,  step_parse),
    2:  (False, step_double),
    3:  (False, step_square),
    4:  (False, step_normalize_minmax),
    5:  (False, step_scale),
    6:  (False, step_round3),
    7:  (False, step_moving_avg_3),
    8:  (False, step_cumsum),
    9:  (False, step_diffs),
    10: (False, step_prefix_min),
    11: (False, step_abs),
    12: (False, step_sort_desc),
    13: (False, step_top_k),
    14: (False, step_aggregate),
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="stats_cascade pipeline step executor")
    parser.add_argument("--step",  type=int, required=True,  help="Step number (1-14)")
    parser.add_argument("--in",    dest="input",  required=True, help="Path to input JSON")
    parser.add_argument("--out",   dest="output", required=True, help="Path to output JSON")
    args = parser.parse_args()

    # Read raw bytes for provenance, then parse JSON
    raw_bytes = open(args.input, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    obj = json.loads(raw_bytes)

    if args.step not in STEPS:
        raise ValueError(f"Unknown step: {args.step}. Must be 1-14.")

    reads_values, fn = STEPS[args.step]

    if reads_values:
        # Step 1: input file has {"values": [...]}
        result = fn(obj)
    else:
        # Steps 2-14: input file has {"step": K, "data": [...], "provenance": "..."}
        result = fn(obj["data"])

    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.output, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
