"""Deliberately-broken reference for long_horizon/lh10_mega_etl.

Planted defects:
  * Step 16 (filter_gt_mean): keeps elements <= mean instead of > mean (inverted filter).
  * Step 19 (top_k): returns the LAST 5 elements (smallest) instead of first 5 (largest).

Steps 1-15 and 17-18 and 20 are correct. The grader must fail >=1 step (not step 1).
"""
from __future__ import annotations

import argparse
import hashlib
import json


def step1_parse(prev: dict) -> list:
    return [float(v) for v in prev["values"]]


def step2_add_const(prev: dict) -> list:
    return [v + 7.0 for v in prev["data"]]


def step3_double(prev: dict) -> list:
    return [v * 2.0 for v in prev["data"]]


def step4_mod(prev: dict) -> list:
    return [v % 11 for v in prev["data"]]


def step5_scale_by_index(prev: dict) -> list:
    return [(i + 1) * v for i, v in enumerate(prev["data"])]


def step6_cumsum(prev: dict) -> list:
    result = []
    total = 0.0
    for v in prev["data"]:
        total += v
        result.append(total)
    return result


def step7_prefix_max(prev: dict) -> list:
    result = []
    current_max = float("-inf")
    for v in prev["data"]:
        current_max = max(current_max, v)
        result.append(current_max)
    return result


def step8_prefix_min(prev: dict) -> list:
    data = prev["data"]
    n = len(data)
    result = [None] * n
    current_min = float("inf")
    for i in range(n - 1, -1, -1):
        current_min = min(current_min, data[i])
        result[i] = current_min
    return result


def step9_diffs(prev: dict) -> list:
    data = prev["data"]
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step10_abs(prev: dict) -> list:
    return [abs(v) for v in prev["data"]]


def step11_square(prev: dict) -> list:
    return [v * v for v in prev["data"]]


def step12_normalize_minmax(prev: dict) -> list:
    data = prev["data"]
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step13_scale(prev: dict) -> list:
    return [v * 1000.0 for v in prev["data"]]


def step14_round3(prev: dict) -> list:
    return [round(v, 3) for v in prev["data"]]


def step15_moving_avg_3(prev: dict) -> list:
    data = prev["data"]
    result = []
    for i, v in enumerate(data):
        if i == 0:
            result.append(float(v))
        elif i == 1:
            result.append((data[0] + data[1]) / 2.0)
        else:
            result.append((data[i - 2] + data[i - 1] + data[i]) / 3.0)
    return result


def step16_filter_gt_mean(prev: dict) -> list:
    """BUG: keeps elements <= mean instead of > mean (inverted filter)."""
    data = prev["data"]
    mean = sum(data) / len(data)
    return [v for v in data if v <= mean]  # BUG: inverted condition


def step17_sort_desc(prev: dict) -> list:
    return sorted(prev["data"], reverse=True)


def step18_dedupe(prev: dict) -> list:
    seen: set = set()
    result = []
    for v in prev["data"]:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def step19_top_k(prev: dict) -> list:
    """BUG: returns last 5 (smallest) instead of first 5 (largest)."""
    return prev["data"][-5:]  # BUG: should be [:5]


def step20_aggregate(prev: dict) -> dict:
    data = prev["data"]
    return {
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "count": len(data),
    }


STEPS = {
    1: step1_parse,
    2: step2_add_const,
    3: step3_double,
    4: step4_mod,
    5: step5_scale_by_index,
    6: step6_cumsum,
    7: step7_prefix_max,
    8: step8_prefix_min,
    9: step9_diffs,
    10: step10_abs,
    11: step11_square,
    12: step12_normalize_minmax,
    13: step13_scale,
    14: step14_round3,
    15: step15_moving_avg_3,
    16: step16_filter_gt_mean,
    17: step17_sort_desc,
    18: step18_dedupe,
    19: step19_top_k,
    20: step20_aggregate,
}


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    if args.step not in STEPS:
        print(f"Unknown step: {args.step}", flush=True)
        return 1

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = STEPS[args.step](prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
