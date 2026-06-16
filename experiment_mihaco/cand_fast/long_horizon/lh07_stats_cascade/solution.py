"""
stats_cascade — 14-step numerical pipeline
Each step reads the previous step's output JSON and writes its result.
"""

import argparse
import hashlib
import json


def compute_provenance(in_path: str) -> str:
    """Hash the exact bytes of the input file for provenance."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(in_data):
    """Read 'values' key and cast each element to float."""
    return [float(x) for x in in_data["values"]]


def step2_double(in_data):
    """Multiply every element by 2."""
    lst = in_data["data"]
    return [x * 2 for x in lst]


def step3_square(in_data):
    """Raise every element to the power of 2."""
    lst = in_data["data"]
    return [x * x for x in lst]


def step4_normalize_minmax(in_data):
    """Apply min-max normalization."""
    lst = in_data["data"]
    mn = min(lst)
    mx = max(lst)
    return [(x - mn) / (mx - mn) for x in lst]


def step5_scale(in_data):
    """Multiply every element by 50."""
    lst = in_data["data"]
    return [x * 50 for x in lst]


def step6_round3(in_data):
    """Round every element to 3 decimal places using Python's built-in round()."""
    lst = in_data["data"]
    return [round(x, 3) for x in lst]


def step7_moving_avg_3(in_data):
    """Apply a 3-element moving average with variable window at boundaries."""
    lst = in_data["data"]
    result = []
    for i in range(len(lst)):
        window = lst[max(0, i - 2):i + 1]
        result.append(sum(window) / len(window))
    return result


def step8_cumsum(in_data):
    """Compute running cumulative sum."""
    lst = in_data["data"]
    result = []
    total = 0.0
    for x in lst:
        total += x
        result.append(total)
    return result


def step9_diffs(in_data):
    """Compute consecutive differences; result is one shorter."""
    lst = in_data["data"]
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


def step10_prefix_min(in_data):
    """Compute running prefix minimum."""
    lst = in_data["data"]
    result = []
    cur = lst[0]
    result.append(cur)
    for x in lst[1:]:
        cur = min(cur, x)
        result.append(cur)
    return result


def step11_abs(in_data):
    """Take the absolute value of every element."""
    lst = in_data["data"]
    return [abs(x) for x in lst]


def step12_sort_desc(in_data):
    """Sort the list in descending order."""
    lst = in_data["data"]
    return sorted(lst, reverse=True)


def step13_top_k(in_data):
    """Keep only the first 8 elements (top-8 largest from sorted desc list)."""
    lst = in_data["data"]
    return lst[:8]


def step14_aggregate(in_data):
    """Compute summary statistics over the 8-element list."""
    lst = in_data["data"]
    n = len(lst)
    s = sum(lst)
    return {
        "sum": s,
        "mean": s / n,
        "min": min(lst),
        "max": max(lst),
        "count": int(n),
    }


STEP_FUNCTIONS = {
    1: step1_parse,
    2: step2_double,
    3: step3_square,
    4: step4_normalize_minmax,
    5: step5_scale,
    6: step6_round3,
    7: step7_moving_avg_3,
    8: step8_cumsum,
    9: step9_diffs,
    10: step10_prefix_min,
    11: step11_abs,
    12: step12_sort_desc,
    13: step13_top_k,
    14: step14_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="stats_cascade pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-14)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Compute provenance from raw bytes BEFORE parsing
    provenance = compute_provenance(args.in_path)

    # Parse the input JSON
    with open(args.in_path, 'r') as f:
        in_data = json.load(f)

    # Dispatch to the correct step function
    step_fn = STEP_FUNCTIONS.get(args.step)
    if step_fn is None:
        raise ValueError(f"Unknown step: {args.step}")

    result = step_fn(in_data)

    # Write output
    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, 'w') as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
