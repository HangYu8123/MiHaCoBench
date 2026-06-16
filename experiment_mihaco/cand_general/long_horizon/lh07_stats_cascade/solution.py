"""
stats_cascade — 14-step numerical pipeline
CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def step1_parse(in_data):
    """Read 'values' from root; cast to float. Result: 18 floats."""
    return [float(v) for v in in_data["values"]]


def step2_double(data):
    """Multiply every element by 2. Result: 18 floats."""
    return [x * 2.0 for x in data]


def step3_square(data):
    """Raise every element to power 2 (x*x). Result: 18 floats."""
    return [x * x for x in data]


def step4_normalize_minmax(data):
    """Min-max normalization: (x-min)/(max-min). Result: 18 floats in [0,1]."""
    mn = min(data)
    mx = max(data)
    return [(x - mn) / (mx - mn) for x in data]


def step5_scale(data):
    """Multiply every element by 50. Result: 18 floats."""
    return [x * 50.0 for x in data]


def step6_round3(data):
    """Round every element to 3 decimal places. Result: 18 floats."""
    return [round(x, 3) for x in data]


def step7_moving_avg_3(data):
    """
    3-element moving average with spec-defined window:
      i == 0: window = [data[0]]
      i == 1: window = [data[0], data[1]]
      i >= 2: window = [data[i-2], data[i-1], data[i]]
    Value = sum(window) / len(window).
    Result: 18 floats.
    """
    out = []
    for i in range(len(data)):
        if i == 0:
            window = [data[0]]
        elif i == 1:
            window = [data[0], data[1]]
        else:
            window = [data[i - 2], data[i - 1], data[i]]
        out.append(sum(window) / len(window))
    return out


def step8_cumsum(data):
    """Running cumulative sum. out[i] = sum(data[0..i]). Result: 18 floats."""
    out = []
    acc = 0.0
    for x in data:
        acc += x
        out.append(acc)
    return out


def step9_diffs(data):
    """Consecutive differences. out[i] = data[i+1]-data[i]. Result: 17 floats."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step10_prefix_min(data):
    """Running prefix minimum. out[i] = min(data[0..i]). Result: 17 floats."""
    cur = data[0]
    out = [cur]
    for x in data[1:]:
        cur = min(cur, x)
        out.append(cur)
    return out


def step11_abs(data):
    """Absolute value of every element. Result: 17 floats."""
    return [abs(x) for x in data]


def step12_sort_desc(data):
    """Sort in descending order. Result: 17 floats."""
    return sorted(data, reverse=True)


def step13_top_k(data):
    """Keep first 8 elements (top-8 largest, already sorted desc). Result: 8 floats."""
    return data[:8]


def step14_aggregate(data):
    """
    Summary statistics over 8-element list.
    Result dict: sum (float), mean (float), min (float), max (float), count (int=8).
    """
    n = len(data)
    return {
        "sum": sum(data),
        "mean": sum(data) / n,
        "min": min(data),
        "max": max(data),
        "count": n,  # len() returns int natively
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

STEPS = {
    1:  step1_parse,
    2:  step2_double,
    3:  step3_square,
    4:  step4_normalize_minmax,
    5:  step5_scale,
    6:  step6_round3,
    7:  step7_moving_avg_3,
    8:  step8_cumsum,
    9:  step9_diffs,
    10: step10_prefix_min,
    11: step11_abs,
    12: step12_sort_desc,
    13: step13_top_k,
    14: step14_aggregate,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="stats_cascade pipeline step runner")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-14)")
    # '--in' would cause argparse to derive dest='in' which is a Python keyword;
    # explicit dest='in_path' avoids that conflict.
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    step_num = args.step

    if step_num not in STEPS:
        print(f"Error: step {step_num} is not valid (must be 1-14)", file=sys.stderr)
        sys.exit(1)

    # Read raw bytes first for provenance hash
    with open(args.in_path, "rb") as fraw:
        raw_bytes = fraw.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON from the same bytes
    in_data = json.loads(raw_bytes)

    # Step 1 reads `in_data["values"]` at root; all others read `in_data["data"]`
    if step_num == 1:
        result = STEPS[1](in_data)
    else:
        data = in_data["data"]
        result = STEPS[step_num](data)

    # Build output with keys in spec order: step, data, provenance
    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out, "w") as fout:
        json.dump(output, fout)


if __name__ == "__main__":
    main()
