import argparse
import hashlib
import json


def step1_parse_float(input_data):
    return [float(v) for v in input_data["values"]]


def step2_normalize_minmax(data):
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step3_scale(data):
    return [v * 100 for v in data]


def step4_round3(data):
    return [round(v, 3) for v in data]


def step5_moving_avg_3(data):
    return [(data[i] + data[i+1] + data[i+2]) / 3 for i in range(len(data) - 2)]


def step6_square(data):
    return [v * v for v in data]


def step7_prefix_max(data):
    result = []
    current_max = data[0]
    for v in data:
        if v > current_max:
            current_max = v
        result.append(current_max)
    return result


def step8_diffs(data):
    return [data[i+1] - data[i] for i in range(len(data) - 1)]


def step9_sort_desc(data):
    return sorted(data, reverse=True)


def step10_aggregate(data):
    s = sum(data)
    c = int(len(data))
    return {
        "sum": s,
        "mean": s / c,
        "min": min(data),
        "max": max(data),
        "count": c,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", dest="output", required=True)
    args = parser.parse_args()

    # Read raw bytes for provenance hash, then parse JSON
    with open(args.input, "rb") as f:
        raw_bytes = f.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()
    input_json = json.loads(raw_bytes)

    k = args.step

    if k == 1:
        result = step1_parse_float(input_json)
    else:
        data = input_json["data"]
        if k == 2:
            result = step2_normalize_minmax(data)
        elif k == 3:
            result = step3_scale(data)
        elif k == 4:
            result = step4_round3(data)
        elif k == 5:
            result = step5_moving_avg_3(data)
        elif k == 6:
            result = step6_square(data)
        elif k == 7:
            result = step7_prefix_max(data)
        elif k == 8:
            result = step8_diffs(data)
        elif k == 9:
            result = step9_sort_desc(data)
        elif k == 10:
            result = step10_aggregate(data)
        else:
            raise ValueError(f"Unknown step: {k}")

    output = {"step": k, "data": result, "provenance": provenance}

    with open(args.output, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
