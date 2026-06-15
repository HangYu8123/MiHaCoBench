"""Deliberately-broken reference for long_horizon/lh07_stats_cascade.

Planted defects (two, either one would be caught):
  1. step3_square uses x*2 (double) instead of x*x (square) — wrong from step 3 onward.
  2. step13_top_k returns the LAST 8 elements (smallest) instead of the FIRST 8 (largest).
Both defects cause the grader to fail at least on step 3 and step 13.
Step 1 is correct to demonstrate partial credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json


def step1_parse(prev: dict) -> list:
    """Cast each value in 'values' to float."""
    return [float(v) for v in prev["values"]]


def step2_double(prev: dict) -> list:
    """Multiply every element by 2."""
    return [v * 2 for v in prev["data"]]


def step3_square(prev: dict) -> list:
    """BUG: uses x*2 (double again) instead of x*x (square)."""
    return [v * 2 for v in prev["data"]]  # BUG: should be v * v


def step4_normalize_minmax(prev: dict) -> list:
    """Min-max normalization."""
    xs = list(prev["data"])
    mn = min(xs)
    mx = max(xs)
    denom = mx - mn
    return [(v - mn) / denom for v in xs]


def step5_scale(prev: dict) -> list:
    """Multiply every element by 50."""
    return [v * 50 for v in prev["data"]]


def step6_round3(prev: dict) -> list:
    """Round every element to 3 decimal places."""
    return [round(v, 3) for v in prev["data"]]


def step7_moving_avg_3(prev: dict) -> list:
    """3-element moving average with truncated windows at the start."""
    lst = list(prev["data"])
    out = []
    for i in range(len(lst)):
        if i == 0:
            window = lst[0:1]
        elif i == 1:
            window = lst[0:2]
        else:
            window = lst[i - 2:i + 1]
        out.append(sum(window) / len(window))
    return out


def step8_cumsum(prev: dict) -> list:
    """Running cumulative sum."""
    out = []
    total = 0.0
    for v in prev["data"]:
        total += v
        out.append(total)
    return out


def step9_diffs(prev: dict) -> list:
    """Consecutive differences."""
    lst = list(prev["data"])
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


def step10_prefix_min(prev: dict) -> list:
    """Running prefix minimum."""
    out = []
    cur_min = float("inf")
    for v in prev["data"]:
        cur_min = min(cur_min, v)
        out.append(cur_min)
    return out


def step11_abs(prev: dict) -> list:
    """Absolute value of every element."""
    return [abs(v) for v in prev["data"]]


def step12_sort_desc(prev: dict) -> list:
    """Sort in descending order."""
    return sorted(prev["data"], reverse=True)


def step13_top_k(prev: dict) -> list:
    """BUG: returns LAST 8 elements (smallest) instead of FIRST 8 (largest)."""
    return list(prev["data"])[-8:]  # BUG: should be [:8]


def step14_aggregate(prev: dict) -> dict:
    """Summary statistics: sum, mean, min, max, count."""
    xs = list(prev["data"])
    return {
        "sum": sum(xs),
        "mean": sum(xs) / len(xs),
        "min": min(xs),
        "max": max(xs),
        "count": len(xs),
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


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="14-step numerical stats cascade pipeline.")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = STEPS[args.step](prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
