"""Deliberately-broken reference for long_horizon/lh05_signal_chain.

Planted defect: step 5 uses a sliding window of width 2 instead of 3.
This produces a list of length 11 (not 10) with wrong values, which
cascades through steps 6-10. Steps 1-4 are correct; steps 5-10 fail.
MUST fail the grader.
"""
from __future__ import annotations

import argparse
import hashlib
import json


def step1_parse_float(prev: dict) -> list:
    return [float(v) for v in prev["values"]]


def step2_normalize_minmax(prev: dict) -> list:
    xs = list(prev["data"])
    mn = min(xs)
    mx = max(xs)
    if mx == mn:
        return [0.0] * len(xs)
    return [(v - mn) / (mx - mn) for v in xs]


def step3_scale(prev: dict) -> list:
    return [v * 100.0 for v in prev["data"]]


def step4_round3(prev: dict) -> list:
    return [round(v, 3) for v in prev["data"]]


def step5_moving_avg_3(prev: dict) -> list:
    """BUG: uses window size 2 instead of 3; produces wrong length and values."""
    xs = list(prev["data"])
    # BUG: window=2 → length 11, not 10; and values are wrong
    return [(xs[i] + xs[i + 1]) / 2.0 for i in range(len(xs) - 1)]


def step6_square(prev: dict) -> list:
    return [v * v for v in prev["data"]]


def step7_prefix_max(prev: dict) -> list:
    xs = list(prev["data"])
    result = []
    cur_max = None
    for v in xs:
        if cur_max is None or v > cur_max:
            cur_max = v
        result.append(cur_max)
    return result


def step8_diffs(prev: dict) -> list:
    xs = list(prev["data"])
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def step9_sort_desc(prev: dict) -> list:
    return sorted(prev["data"], reverse=True)


def step10_aggregate(prev: dict) -> dict:
    xs = list(prev["data"])
    n = len(xs)
    return {
        "sum": sum(xs),
        "mean": sum(xs) / n if n else 0.0,
        "min": min(xs),
        "max": max(xs),
        "count": n,
    }


STEPS = {
    1: step1_parse_float,
    2: step2_normalize_minmax,
    3: step3_scale,
    4: step4_round3,
    5: step5_moving_avg_3,
    6: step6_square,
    7: step7_prefix_max,
    8: step8_diffs,
    9: step9_sort_desc,
    10: step10_aggregate,
}


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    fn = STEPS.get(args.step)
    if fn is None:
        raise ValueError(f"unknown step {args.step}")
    data = fn(prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
