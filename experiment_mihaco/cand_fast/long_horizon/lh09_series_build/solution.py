import argparse
import hashlib
import json


def step1_parse_float(values):
    return [float(v) for v in values]


def step2_double(data):
    return [v * 2 for v in data]


def step3_add_const(data):
    return [v + 2 for v in data]


def step4_cumsum(data):
    result = []
    total = 0.0
    for v in data:
        total += v
        result.append(total)
    return result


def step5_mod(data):
    return [v % 13 for v in data]


def step6_scale_by_index(data):
    return [v * i for i, v in enumerate(data)]


def step7_prefix_max(data):
    result = []
    cur_max = data[0]
    for v in data:
        if v > cur_max:
            cur_max = v
        result.append(cur_max)
    return result


def step8_diffs(data):
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step9_abs(data):
    return [abs(v) for v in data]


def step10_filter_gt_mean(data):
    mean = sum(data) / len(data)
    return [v for v in data if v > mean]


def step11_square(data):
    return [v ** 2 for v in data]


def step12_normalize_minmax(data):
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0 for _ in data]
    return [(v - mn) / (mx - mn) for v in data]


def step13_scale(data):
    return [v * 100 for v in data]


def step14_round3(data):
    return [round(v, 3) for v in data]


def step15_moving_avg_3(data):
    result = []
    for i in range(len(data)):
        if i < 2:
            result.append(data[i])
        else:
            result.append((data[i - 2] + data[i - 1] + data[i]) / 3)
    return result


def step16_sort_desc(data):
    return sorted(data, reverse=True)


def step17_top_k(data):
    return data[:6]


def step18_aggregate(data):
    total = sum(data)
    count = len(data)
    return {
        "sum": float(total),
        "mean": float(total / count),
        "count": int(count),
        "min": float(min(data)),
        "max": float(max(data)),
    }


STEP_FUNCS = {
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    raw_bytes = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    payload = json.loads(raw_bytes)

    step = args.step
    if step == 1:
        input_data = payload["values"]
    else:
        input_data = payload["data"]

    func = STEP_FUNCS[step]
    result = func(input_data)

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        f.write(json.dumps(output))


if __name__ == "__main__":
    main()
