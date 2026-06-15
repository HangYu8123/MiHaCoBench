"""Deliberately-broken reference for long_horizon/lh08_token_pipeline.

Planted defect: step 4 uses mod(7) instead of mod(5). This corrupts the values
from step 4 onward, causing every downstream step to produce wrong results. Step
1 (parse) stays correct, so the grader awards partial credit for that step only
and fails on steps 4-16.

MUST fail the grader on at least step 4.
"""
from __future__ import annotations

import argparse
import hashlib
import json


def step1_parse(prev: dict) -> list:
    return [float(v) for v in prev["values"]]


def step2_add_const(prev: dict) -> list:
    return [v + 1.0 for v in prev["data"]]


def step3_double(prev: dict) -> list:
    return [v * 2.0 for v in prev["data"]]


def step4_mod(prev: dict) -> list:
    # BUG: uses mod 7 instead of mod 5
    return [v % 7 for v in prev["data"]]


def step5_scale_by_index(prev: dict) -> list:
    return [v * i for i, v in enumerate(prev["data"])]


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


def step8_diffs(prev: dict) -> list:
    data = prev["data"]
    return [data[i] - data[i - 1] for i in range(1, len(data))]


def step9_abs(prev: dict) -> list:
    return [abs(v) for v in prev["data"]]


def step10_square(prev: dict) -> list:
    return [v * v for v in prev["data"]]


def step11_normalize_minmax(prev: dict) -> list:
    data = prev["data"]
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step12_scale(prev: dict) -> list:
    return [v * 10.0 for v in prev["data"]]


def step13_round3(prev: dict) -> list:
    return [round(v, 3) for v in prev["data"]]


def step14_sort_asc(prev: dict) -> list:
    return sorted(prev["data"])


def step15_dedupe(prev: dict) -> list:
    result = []
    for v in prev["data"]:
        if not result or result[-1] != v:
            result.append(v)
    return result


def step16_aggregate(prev: dict) -> dict:
    data = prev["data"]
    count = len(data)
    total = sum(data)
    return {
        "sum": total,
        "mean": total / count if count else 0.0,
        "max": max(data),
        "min": min(data),
        "count": count,
    }


STEPS = {
    1: step1_parse,
    2: step2_add_const,
    3: step3_double,
    4: step4_mod,
    5: step5_scale_by_index,
    6: step6_cumsum,
    7: step7_prefix_max,
    8: step8_diffs,
    9: step9_abs,
    10: step10_square,
    11: step11_normalize_minmax,
    12: step12_scale,
    13: step13_round3,
    14: step14_sort_asc,
    15: step15_dedupe,
    16: step16_aggregate,
}


def _provenance(in_path: str) -> str:
    with open(in_path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    with open(args.in_path, encoding="utf-8") as fh:
        prev = json.load(fh)

    data = STEPS[args.step](prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}

    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
