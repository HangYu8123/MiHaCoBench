"""Gold reference for long_horizon/lh10_mega_etl — a 20-step ETL provenance chain.

Each step reads --in (the previous step's artifact), applies one transform, and
writes --out with keys {"step", "data", "provenance"} where provenance is the
SHA-256 of the consumed file.
"""
from __future__ import annotations

import argparse
import hashlib
import json


# --------------------------------------------------------------------------- #
# Step implementations
# --------------------------------------------------------------------------- #

def step1_parse(prev: dict) -> list:
    """Cast each integer in 'values' to float."""
    return [float(v) for v in prev["values"]]


def step2_add_const(prev: dict) -> list:
    """Add 7 to every element."""
    return [v + 7.0 for v in prev["data"]]


def step3_double(prev: dict) -> list:
    """Multiply every element by 2."""
    return [v * 2.0 for v in prev["data"]]


def step4_mod(prev: dict) -> list:
    """Apply modulo 11 (floating-point %) to every element."""
    return [v % 11 for v in prev["data"]]


def step5_scale_by_index(prev: dict) -> list:
    """Multiply element at index i by (i + 1) (1-based position)."""
    return [(i + 1) * v for i, v in enumerate(prev["data"])]


def step6_cumsum(prev: dict) -> list:
    """Running cumulative sum."""
    result = []
    total = 0.0
    for v in prev["data"]:
        total += v
        result.append(total)
    return result


def step7_prefix_max(prev: dict) -> list:
    """Running maximum from left: result[k] = max(data[0..k])."""
    result = []
    current_max = float("-inf")
    for v in prev["data"]:
        current_max = max(current_max, v)
        result.append(current_max)
    return result


def step8_prefix_min(prev: dict) -> list:
    """Running minimum from right: result[k] = min(data[k..end])."""
    data = prev["data"]
    n = len(data)
    result = [None] * n
    current_min = float("inf")
    for i in range(n - 1, -1, -1):
        current_min = min(current_min, data[i])
        result[i] = current_min
    return result


def step9_diffs(prev: dict) -> list:
    """Consecutive differences: result[i] = data[i+1] - data[i]."""
    data = prev["data"]
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step10_abs(prev: dict) -> list:
    """Absolute value of every element."""
    return [abs(v) for v in prev["data"]]


def step11_square(prev: dict) -> list:
    """Square every element."""
    return [v * v for v in prev["data"]]


def step12_normalize_minmax(prev: dict) -> list:
    """Min-max normalization to [0, 1]. All-equal input -> all 0.0."""
    data = prev["data"]
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step13_scale(prev: dict) -> list:
    """Multiply every element by 1000."""
    return [v * 1000.0 for v in prev["data"]]


def step14_round3(prev: dict) -> list:
    """Round every element to 3 decimal places."""
    return [round(v, 3) for v in prev["data"]]


def step15_moving_avg_3(prev: dict) -> list:
    """Trailing 3-element moving average with smaller window at start.

    Element 0 -> itself; element 1 -> avg(0, 1); element k >= 2 -> avg(k-2, k-1, k).
    """
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
    """Keep only elements strictly greater than the arithmetic mean."""
    data = prev["data"]
    mean = sum(data) / len(data)
    return [v for v in data if v > mean]


def step17_sort_desc(prev: dict) -> list:
    """Sort in descending order."""
    return sorted(prev["data"], reverse=True)


def step18_dedupe(prev: dict) -> list:
    """Remove duplicate values, keeping the first occurrence in the current order."""
    seen: set = set()
    result = []
    for v in prev["data"]:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def step19_top_k(prev: dict) -> list:
    """Keep the first 5 elements (largest 5, since list is sorted descending)."""
    return prev["data"][:5]


def step20_aggregate(prev: dict) -> dict:
    """Compute sum, mean, min, max, count over the 5 values."""
    data = prev["data"]
    return {
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "count": len(data),
    }


# --------------------------------------------------------------------------- #
# Dispatch table
# --------------------------------------------------------------------------- #
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
    """SHA-256 of the exact bytes of the consumed file."""
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="mega_etl pipeline step runner")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-20)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
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
