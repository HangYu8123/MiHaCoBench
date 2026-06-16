"""
10-step signal processing pipeline.

CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Each step reads the JSON at --in, computes its result, and writes to --out a JSON
object with exactly these keys:
  {"step": <K>, "data": <result>, "provenance": "<sha256 hex of --in file bytes>"}
"""

import argparse
import hashlib
import json
import sys


def step1_parse_float(data):
    """Cast each element in 'values' list to float. Output len 12."""
    return [float(v) for v in data]


def step2_normalize_minmax(data):
    """Min-max normalize. If max == min, return all zeros. Output len 12."""
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step3_scale(data):
    """Multiply each element by 100. Output len 12."""
    return [v * 100.0 for v in data]


def step4_round3(data):
    """Round each element to 3 decimal places using Python built-in round. Output len 12."""
    return [round(v, 3) for v in data]


def step5_moving_avg_3(data):
    """Sliding window mean of width 3. Output len 10 (from len 12)."""
    n = len(data)
    return [(data[i] + data[i + 1] + data[i + 2]) / 3.0 for i in range(n - 2)]


def step6_square(data):
    """Square each element: v * v. Output len 10."""
    return [v * v for v in data]


def step7_prefix_max(data):
    """Running maximum: result[i] = max(data[0..i]). Output len 10."""
    if not data:
        return []
    cur = float(data[0])
    result = [cur]
    for v in data[1:]:
        cur = float(max(cur, v))
        result.append(cur)
    return result


def step8_diffs(data):
    """Consecutive differences: result[i] = data[i+1] - data[i]. Output len 9 (from len 10)."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step9_sort_desc(data):
    """Sort descending. Output len 9."""
    return sorted(data, reverse=True)


def step10_aggregate(data):
    """Summary stats dict with sum, mean, min, max, count."""
    n = len(data)
    return {
        "sum": float(sum(data)),
        "mean": float(sum(data) / n),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": n,
    }


def main():
    parser = argparse.ArgumentParser(description="Signal chain pipeline step executor")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-10)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes for provenance hash, then parse JSON
    raw = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()
    input_json = json.loads(raw)

    step = args.step

    # Step 1 reads from "values" key; steps 2-10 read from "data" key
    if step == 1:
        values = input_json["values"]
        result = step1_parse_float(values)
    elif step == 2:
        d = input_json["data"]
        result = step2_normalize_minmax(d)
    elif step == 3:
        d = input_json["data"]
        result = step3_scale(d)
    elif step == 4:
        d = input_json["data"]
        result = step4_round3(d)
    elif step == 5:
        d = input_json["data"]
        result = step5_moving_avg_3(d)
    elif step == 6:
        d = input_json["data"]
        result = step6_square(d)
    elif step == 7:
        d = input_json["data"]
        result = step7_prefix_max(d)
    elif step == 8:
        d = input_json["data"]
        result = step8_diffs(d)
    elif step == 9:
        d = input_json["data"]
        result = step9_sort_desc(d)
    elif step == 10:
        d = input_json["data"]
        result = step10_aggregate(d)
    else:
        print(f"Error: invalid step {step}. Must be 1-10.", file=sys.stderr)
        sys.exit(1)

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
