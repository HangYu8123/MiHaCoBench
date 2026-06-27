"""
stats_cascade — 14-step numerical pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def step_parse(in_path, in_data):
    """Step 1: read 'values' from input and cast to float."""
    return [float(x) for x in in_data["values"]]


def step_double(in_path, in_data):
    """Step 2: multiply every element by 2."""
    data = in_data["data"]
    return [x * 2 for x in data]


def step_square(in_path, in_data):
    """Step 3: raise every element to the power of 2."""
    data = in_data["data"]
    return [x * x for x in data]


def step_normalize_minmax(in_path, in_data):
    """Step 4: min-max normalization."""
    data = in_data["data"]
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(x - mn) / (mx - mn) for x in data]


def step_scale(in_path, in_data):
    """Step 5: multiply every element by 50."""
    data = in_data["data"]
    return [x * 50 for x in data]


def step_round3(in_path, in_data):
    """Step 6: round every element to 3 decimal places."""
    data = in_data["data"]
    return [round(x, 3) for x in data]


def step_moving_avg_3(in_path, in_data):
    """Step 7: 3-element moving average."""
    data = in_data["data"]
    result = []
    for i in range(len(data)):
        window = data[max(0, i - 2): i + 1]
        result.append(sum(window) / len(window))
    return result


def step_cumsum(in_path, in_data):
    """Step 8: cumulative sum."""
    data = in_data["data"]
    running = 0.0
    out = []
    for x in data:
        running += x
        out.append(running)
    return out


def step_diffs(in_path, in_data):
    """Step 9: consecutive differences (length - 1 elements)."""
    data = in_data["data"]
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_prefix_min(in_path, in_data):
    """Step 10: running prefix minimum."""
    data = in_data["data"]
    cur = data[0]
    out = [cur]
    for x in data[1:]:
        cur = min(cur, x)
        out.append(cur)
    return out


def step_abs(in_path, in_data):
    """Step 11: absolute value of every element."""
    data = in_data["data"]
    return [abs(x) for x in data]


def step_sort_desc(in_path, in_data):
    """Step 12: sort in descending order."""
    data = in_data["data"]
    return sorted(data, reverse=True)


def step_top_k(in_path, in_data):
    """Step 13: keep first 8 elements."""
    data = in_data["data"]
    return data[:8]


def step_aggregate(in_path, in_data):
    """Step 14: compute summary statistics."""
    data = in_data["data"]
    n = len(data)
    total = sum(data)
    return {
        "sum": total,
        "mean": total / n,
        "min": min(data),
        "max": max(data),
        "count": int(n),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

STEPS = {
    1: step_parse,
    2: step_double,
    3: step_square,
    4: step_normalize_minmax,
    5: step_scale,
    6: step_round3,
    7: step_moving_avg_3,
    8: step_cumsum,
    9: step_diffs,
    10: step_prefix_min,
    11: step_abs,
    12: step_sort_desc,
    13: step_top_k,
    14: step_aggregate,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="stats_cascade pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-14)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes for provenance hash BEFORE parsing JSON
    with open(args.in_path, "rb") as f:
        raw_bytes = f.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON
    in_data = json.loads(raw_bytes)

    # Dispatch to the appropriate step handler
    handler = STEPS[args.step]
    result = handler(args.in_path, in_data)

    # Write output
    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
