import argparse
import hashlib
import json


def step_parse(prev):
    return [float(x) for x in prev["values"]]


def step_double(prev):
    return [x * 2.0 for x in prev["data"]]


def step_add_const(prev):
    return [x + 3.0 for x in prev["data"]]


def step_filter_gt_mean(prev):
    lst = prev["data"]
    mean = sum(lst) / len(lst)
    return [x for x in lst if x > mean]


def step_sort_desc(prev):
    return sorted(prev["data"], reverse=True)


def step_aggregate(prev):
    lst = prev["data"]
    total = sum(lst)
    n = len(lst)
    return {
        "sum": float(total),
        "mean": float(total) / n,
        "min": float(min(lst)),
        "max": float(max(lst)),
        "count": int(n),
    }


STEPS = {
    1: step_parse,
    2: step_double,
    3: step_add_const,
    4: step_filter_gt_mean,
    5: step_sort_desc,
    6: step_aggregate,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    raw = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()
    prev = json.loads(raw)

    step_fn = STEPS[args.step]
    data = step_fn(prev)

    result = {"step": args.step, "data": data, "provenance": provenance}
    with open(args.out, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
