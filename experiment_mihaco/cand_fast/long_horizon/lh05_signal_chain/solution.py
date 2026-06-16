"""
Long-Horizon 05 - signal_chain (10 steps)
10-step signal processing pipeline.
"""

import argparse
import hashlib
import json


def compute_provenance(in_path):
    """Compute sha256 of the exact bytes of the input file."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_parse_float(data):
    """Step 1: Cast each element of 'values' to float."""
    return [float(v) for v in data["values"]]


def step2_normalize_minmax(lst):
    """Step 2: (v - min) / (max - min) per element; all zeros if max == min."""
    min_v = min(lst)
    max_v = max(lst)
    if max_v == min_v:
        return [0.0] * len(lst)
    return [(v - min_v) / (max_v - min_v) for v in lst]


def step3_scale(lst):
    """Step 3: Multiply each element by 100."""
    return [v * 100 for v in lst]


def step4_round3(lst):
    """Step 4: Round each element to 3 decimal places using Python built-in round."""
    return [round(v, 3) for v in lst]


def step5_moving_avg_3(lst):
    """Step 5: Sliding window mean of width 3. Output length = len(lst) - 2."""
    return [(lst[i] + lst[i+1] + lst[i+2]) / 3 for i in range(len(lst) - 2)]


def step6_square(lst):
    """Step 6: Square each element."""
    return [v * v for v in lst]


def step7_prefix_max(lst):
    """Step 7: Running maximum: result[i] = max(data[0..i])."""
    result = []
    current_max = None
    for v in lst:
        if current_max is None or v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step8_diffs(lst):
    """Step 8: Consecutive differences: result[i] = data[i+1] - data[i]."""
    return [lst[i+1] - lst[i] for i in range(len(lst) - 1)]


def step9_sort_desc(lst):
    """Step 9: Sort descending."""
    return sorted(lst, reverse=True)


def step10_aggregate(lst):
    """Step 10: Summary statistics dict."""
    count = int(len(lst))
    total = sum(lst)
    return {
        "sum": float(total),
        "mean": float(total / count),
        "min": float(min(lst)),
        "max": float(max(lst)),
        "count": count,
    }


def main():
    parser = argparse.ArgumentParser(description="Signal chain pipeline step runner")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-10)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Compute provenance from the raw bytes of the input file BEFORE parsing
    provenance = compute_provenance(args.in_path)

    # Load the input JSON
    with open(args.in_path, 'r') as f:
        input_data = json.load(f)

    # Step 1 reads "values" from the raw input; steps 2-10 read "data" from prior artifact
    if args.step == 1:
        lst = input_data["values"]
        result = step1_parse_float({"values": lst})
    else:
        lst = input_data["data"]
        if args.step == 2:
            result = step2_normalize_minmax(lst)
        elif args.step == 3:
            result = step3_scale(lst)
        elif args.step == 4:
            result = step4_round3(lst)
        elif args.step == 5:
            result = step5_moving_avg_3(lst)
        elif args.step == 6:
            result = step6_square(lst)
        elif args.step == 7:
            result = step7_prefix_max(lst)
        elif args.step == 8:
            result = step8_diffs(lst)
        elif args.step == 9:
            result = step9_sort_desc(lst)
        elif args.step == 10:
            result = step10_aggregate(lst)
        else:
            raise ValueError(f"Unknown step: {args.step}")

    # Write the output artifact
    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, 'w') as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
