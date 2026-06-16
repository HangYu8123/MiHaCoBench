"""
Long-Horizon 09 — series_build (18 steps)

CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json


def step1_parse_float(json_data):
    values = json_data["values"]
    return [float(v) for v in values]


def step2_double(json_data):
    data = json_data["data"]
    return [v * 2 for v in data]


def step3_add_const(json_data):
    data = json_data["data"]
    return [v + 2 for v in data]


def step4_cumsum(json_data):
    data = json_data["data"]
    result = []
    acc = 0.0
    for v in data:
        acc += v
        result.append(acc)
    return result


def step5_mod(json_data):
    data = json_data["data"]
    return [v % 13 for v in data]


def step6_scale_by_index(json_data):
    data = json_data["data"]
    return [v * i for i, v in enumerate(data)]


def step7_prefix_max(json_data):
    data = json_data["data"]
    result = []
    current_max = None
    for v in data:
        if current_max is None or v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step8_diffs(json_data):
    data = json_data["data"]
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step9_abs(json_data):
    data = json_data["data"]
    return [abs(v) for v in data]


def step10_filter_gt_mean(json_data):
    data = json_data["data"]
    mean = sum(data) / len(data)
    return [v for v in data if v > mean]


def step11_square(json_data):
    data = json_data["data"]
    return [v * v for v in data]


def step12_normalize_minmax(json_data):
    data = json_data["data"]
    mn = min(data)
    mx = max(data)
    if mn == mx:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step13_scale(json_data):
    data = json_data["data"]
    return [v * 100 for v in data]


def step14_round3(json_data):
    data = json_data["data"]
    return [round(v, 3) for v in data]


def step15_moving_avg_3(json_data):
    data = json_data["data"]
    result = []
    for i, v in enumerate(data):
        if i < 2:
            result.append(v)
        else:
            result.append((data[i - 2] + data[i - 1] + data[i]) / 3.0)
    return result


def step16_sort_desc(json_data):
    data = json_data["data"]
    return sorted(data, reverse=True)


def step17_top_k(json_data):
    data = json_data["data"]
    return data[:6]


def step18_aggregate(json_data):
    data = json_data["data"]
    total = sum(data)
    count = len(data)
    return {
        "sum": float(total),
        "mean": float(total / count),
        "count": int(count),
        "min": float(min(data)),
        "max": float(max(data)),
    }


STEPS = {
    1: step1_parse_float,
    2: step2_double,
    3: step3_add_const,
    4: step4_cumsum,
    5: step5_mod,
    6: step6_scale_by_index,
    7: step7_prefix_max,
    8: step8_diffs,
    9: step9_abs,
    10: step10_filter_gt_mean,
    11: step11_square,
    12: step12_normalize_minmax,
    13: step13_scale,
    14: step14_round3,
    15: step15_moving_avg_3,
    16: step16_sort_desc,
    17: step17_top_k,
    18: step18_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="series_build pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-18)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes first for provenance, then parse JSON from the same bytes
    raw = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()
    json_data = json.loads(raw)

    step_fn = STEPS[args.step]
    result = step_fn(json_data)

    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
