"""
stats_cascade — 14-step numerical pipeline
Usage: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse(data):
    """read values from input; cast each element to float."""
    return [float(x) for x in data["values"]]


def step2_double(data):
    """multiply every element by 2."""
    return [x * 2.0 for x in data]


def step3_square(data):
    """raise every element to the power of 2."""
    return [x * x for x in data]


def step4_normalize_minmax(data):
    """apply min-max normalization."""
    mn = min(data)
    mx = max(data)
    denom = mx - mn
    return [(x - mn) / denom for x in data]


def step5_scale(data):
    """multiply every element by 50."""
    return [x * 50.0 for x in data]


def step6_round3(data):
    """round every element to 3 decimal places."""
    return [round(x, 3) for x in data]


def step7_moving_avg_3(data):
    """apply a 3-element moving average."""
    result = []
    for i, _ in enumerate(data):
        if i == 0:
            window = [data[0]]
        elif i == 1:
            window = [data[0], data[1]]
        else:
            window = [data[i - 2], data[i - 1], data[i]]
        result.append(sum(window) / len(window))
    return result


def step8_cumsum(data):
    """compute the running cumulative sum."""
    result = []
    running = 0.0
    for x in data:
        running += x
        result.append(running)
    return result


def step9_diffs(data):
    """compute consecutive differences."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step10_prefix_min(data):
    """compute the running prefix minimum."""
    result = []
    current_min = None
    for x in data:
        if current_min is None or x < current_min:
            current_min = x
        result.append(current_min)
    return result


def step11_abs(data):
    """take the absolute value of every element."""
    return [abs(x) for x in data]


def step12_sort_desc(data):
    """sort the list in descending order."""
    return sorted(data, reverse=True)


def step13_top_k(data):
    """keep only the first 8 elements."""
    return data[:8]


def step14_aggregate(data):
    """compute summary statistics over the 8-element list."""
    return {
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "count": len(data),
    }


STEPS = {
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_num not in STEPS:
        print(f"Unknown step: {step_num}", file=sys.stderr)
        sys.exit(1)

    provenance = compute_provenance(in_path)

    with open(in_path, 'r') as f:
        in_obj = json.load(f)

    # For step 1, the input is the original input.json with a "values" key.
    # For all other steps, the input is the previous step's output with a "data" key.
    if step_num == 1:
        input_data = in_obj
    else:
        input_data = in_obj["data"]

    fn = STEPS[step_num]
    result = fn(input_data)

    out_obj = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, 'w') as f:
        json.dump(out_obj, f)


if __name__ == "__main__":
    main()
