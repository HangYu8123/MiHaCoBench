import argparse
import hashlib
import json


def step_parse(data):
    return [float(x) for x in data]


def step_add_const(data):
    return [x + 7.0 for x in data]


def step_double(data):
    return [x * 2 for x in data]


def step_mod(data):
    return [x % 11 for x in data]


def step_scale_by_index(data):
    return [x * (i + 1) for i, x in enumerate(data)]


def step_cumsum(data):
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step_prefix_max(data):
    result = []
    current_max = float('-inf')
    for x in data:
        if x > current_max:
            current_max = x
        result.append(current_max)
    return result


def step_prefix_min(data):
    # suffix-min: result[i] = min(data[i], data[i+1], ..., data[n-1])
    n = len(data)
    result = list(data)
    for i in range(n - 2, -1, -1):
        result[i] = min(data[i], result[i + 1])
    return result


def step_diffs(data):
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_abs(data):
    return [abs(x) for x in data]


def step_square(data):
    return [x * x for x in data]


def step_normalize_minmax(data):
    min_v = min(data)
    max_v = max(data)
    if max_v == min_v:
        return [0.0] * len(data)
    return [(x - min_v) / (max_v - min_v) for x in data]


def step_scale(data):
    return [x * 1000 for x in data]


def step_round3(data):
    return [round(x, 3) for x in data]


def step_moving_avg_3(data):
    n = len(data)
    result = []
    for k in range(n):
        if k == 0:
            result.append(data[0])
        elif k == 1:
            result.append((data[0] + data[1]) / 2)
        else:
            result.append((data[k - 2] + data[k - 1] + data[k]) / 3)
    return result


def step_filter_gt_mean(data):
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step_sort_desc(data):
    return sorted(data, reverse=True)


def step_dedupe(data):
    seen = set()
    out = []
    for x in data:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def step_top_k(data):
    return data[:5]


def step_aggregate(data):
    n = len(data)
    total = sum(data)
    return {
        "sum": float(total),
        "mean": float(total / n),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": 5
    }


STEPS = {
    1: ("parse", step_parse),
    2: ("add_const", step_add_const),
    3: ("double", step_double),
    4: ("mod", step_mod),
    5: ("scale_by_index", step_scale_by_index),
    6: ("cumsum", step_cumsum),
    7: ("prefix_max", step_prefix_max),
    8: ("prefix_min", step_prefix_min),
    9: ("diffs", step_diffs),
    10: ("abs", step_abs),
    11: ("square", step_square),
    12: ("normalize_minmax", step_normalize_minmax),
    13: ("scale", step_scale),
    14: ("round3", step_round3),
    15: ("moving_avg_3", step_moving_avg_3),
    16: ("filter_gt_mean", step_filter_gt_mean),
    17: ("sort_desc", step_sort_desc),
    18: ("dedupe", step_dedupe),
    19: ("top_k", step_top_k),
    20: ("aggregate", step_aggregate),
}


def main():
    parser = argparse.ArgumentParser(description="Mega ETL pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-20)")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file path")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes for provenance hash
    with open(args.input, "rb") as f:
        raw = f.read()
    provenance = hashlib.sha256(raw).hexdigest()

    # Parse JSON input
    inp = json.loads(raw)

    # Get data based on step number
    if args.step == 1:
        data = inp["values"]
    else:
        data = inp["data"]

    # Dispatch to the appropriate step function
    if args.step not in STEPS:
        raise ValueError(f"Unknown step: {args.step}")

    _, func = STEPS[args.step]
    result = func(data)

    # Write output
    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance
    }

    with open(args.out, "w") as f:
        f.write(json.dumps(output))


if __name__ == "__main__":
    main()
