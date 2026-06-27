import argparse
import hashlib
import json


def step_parse(inp):
    return [float(v) for v in inp['values']]


def step_add_const(data):
    return [x + 7.0 for x in data]


def step_double(data):
    return [x * 2 for x in data]


def step_mod(data):
    return [x % 11 for x in data]


def step_scale_by_index(data):
    return [v * (i + 1) for i, v in enumerate(data)]


def step_cumsum(data):
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step_prefix_max(data):
    result = []
    cur_max = float('-inf')
    for x in data:
        cur_max = max(cur_max, x)
        result.append(cur_max)
    return result


def step_prefix_min(data):
    # RIGHT-to-left: result[i] = min(data[i], data[i+1], ..., data[n-1])
    n = len(data)
    result = [0.0] * n
    cur_min = float('inf')
    for i in range(n - 1, -1, -1):
        cur_min = min(cur_min, data[i])
        result[i] = cur_min
    return result


def step_diffs(data):
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_abs(data):
    return [abs(x) for x in data]


def step_square(data):
    return [x * x for x in data]


def step_normalize_minmax(data):
    mn = min(data)
    mx = max(data)
    if mn == mx:
        return [0.0] * len(data)
    return [(x - mn) / (mx - mn) for x in data]


def step_scale(data):
    return [x * 1000 for x in data]


def step_round3(data):
    return [round(x, 3) for x in data]


def step_moving_avg_3(data):
    result = []
    for k, x in enumerate(data):
        if k == 0:
            result.append(data[0])
        elif k == 1:
            result.append((data[0] + data[1]) / 2.0)
        else:
            result.append((data[k - 2] + data[k - 1] + data[k]) / 3.0)
    return result


def step_filter_gt_mean(data):
    # Compute mean over full list first, then filter
    m = sum(data) / len(data)
    return [x for x in data if x > m]


def step_sort_desc(data):
    return sorted(data, reverse=True)


def step_dedupe(data):
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step_top_k(data):
    return data[:5]


def step_aggregate(data):
    total = sum(data)
    n = len(data)
    return {
        "sum": float(total),
        "mean": float(total / n),
        "min": float(min(data)),
        "max": float(max(data)),
        "count": int(n),
    }


HANDLERS = {
    1: lambda inp: step_parse(inp),
    2: lambda inp: step_add_const(inp['data']),
    3: lambda inp: step_double(inp['data']),
    4: lambda inp: step_mod(inp['data']),
    5: lambda inp: step_scale_by_index(inp['data']),
    6: lambda inp: step_cumsum(inp['data']),
    7: lambda inp: step_prefix_max(inp['data']),
    8: lambda inp: step_prefix_min(inp['data']),
    9: lambda inp: step_diffs(inp['data']),
    10: lambda inp: step_abs(inp['data']),
    11: lambda inp: step_square(inp['data']),
    12: lambda inp: step_normalize_minmax(inp['data']),
    13: lambda inp: step_scale(inp['data']),
    14: lambda inp: step_round3(inp['data']),
    15: lambda inp: step_moving_avg_3(inp['data']),
    16: lambda inp: step_filter_gt_mean(inp['data']),
    17: lambda inp: step_sort_desc(inp['data']),
    18: lambda inp: step_dedupe(inp['data']),
    19: lambda inp: step_top_k(inp['data']),
    20: lambda inp: step_aggregate(inp['data']),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--in', dest='input', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    # Read raw bytes for provenance BEFORE any JSON parsing
    raw = open(args.input, 'rb').read()
    prov = hashlib.sha256(raw).hexdigest()
    inp = json.loads(raw)

    handler = HANDLERS[args.step]
    result = handler(inp)

    output = {"step": args.step, "data": result, "provenance": prov}
    with open(args.out, 'w') as f:
        json.dump(output, f)


if __name__ == '__main__':
    main()
