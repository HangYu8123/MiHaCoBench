"""Gold reference for long_horizon/lh09_series_build — an 18-step numeric pipeline.

Each invocation handles exactly one step of the pipeline. Steps are chained by
the test harness, which feeds each step's --out as the next step's --in.

CLI: python solution.py --step <K> --in <prev_artifact> --out <output_artifact>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step1_parse_float(prev: dict) -> list:
    """Cast input integers to floats."""
    return [float(v) for v in prev["values"]]


def step2_double(prev: dict) -> list:
    """Multiply every element by 2."""
    return [v * 2.0 for v in prev["data"]]


def step3_add_const(prev: dict) -> list:
    """Add 2 to every element."""
    return [v + 2.0 for v in prev["data"]]


def step4_cumsum(prev: dict) -> list:
    """Running cumulative sum."""
    xs = list(prev["data"])
    out: list[float] = []
    running = 0.0
    for v in xs:
        running += v
        out.append(running)
    return out


def step5_mod(prev: dict) -> list:
    """Replace every element with v % 13 (Python modulo)."""
    return [v % 13 for v in prev["data"]]


def step6_scale_by_index(prev: dict) -> list:
    """Multiply every element by its 0-based index."""
    return [v * i for i, v in enumerate(prev["data"])]


def step7_prefix_max(prev: dict) -> list:
    """Running prefix maximum."""
    out: list[float] = []
    cur_max = float("-inf")
    for v in prev["data"]:
        cur_max = max(cur_max, v)
        out.append(cur_max)
    return out


def step8_diffs(prev: dict) -> list:
    """Consecutive differences: [s[1]-s[0], s[2]-s[1], ...]."""
    xs = list(prev["data"])
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def step9_abs(prev: dict) -> list:
    """Absolute value of every element."""
    return [abs(v) for v in prev["data"]]


def step10_filter_gt_mean(prev: dict) -> list:
    """Keep only elements strictly greater than the mean."""
    xs = list(prev["data"])
    if not xs:
        return []
    mean = sum(xs) / len(xs)
    return [v for v in xs if v > mean]


def step11_square(prev: dict) -> list:
    """Square every element."""
    return [v * v for v in prev["data"]]


def step12_normalize_minmax(prev: dict) -> list:
    """Min-max normalize to [0, 1]; if all equal, return all zeros."""
    xs = list(prev["data"])
    mn = min(xs)
    mx = max(xs)
    if mx == mn:
        return [0.0 for _ in xs]
    return [(v - mn) / (mx - mn) for v in xs]


def step13_scale(prev: dict) -> list:
    """Multiply every element by 100."""
    return [v * 100.0 for v in prev["data"]]


def step14_round3(prev: dict) -> list:
    """Round every element to 3 decimal places."""
    return [round(v, 3) for v in prev["data"]]


def step15_moving_avg_3(prev: dict) -> list:
    """3-element moving average; indices 0 and 1 pass through unchanged."""
    xs = list(prev["data"])
    out: list[float] = []
    for i, v in enumerate(xs):
        if i < 2:
            out.append(v)
        else:
            out.append((xs[i - 2] + xs[i - 1] + xs[i]) / 3.0)
    return out


def step16_sort_desc(prev: dict) -> list:
    """Sort descending."""
    return sorted(prev["data"], reverse=True)


def step17_top_k(prev: dict) -> list:
    """Keep first 6 elements (or all if fewer)."""
    xs = list(prev["data"])
    return xs[:6]


def step18_aggregate(prev: dict) -> dict:
    """Aggregate: sum, mean, count, min, max."""
    xs = list(prev["data"])
    total = sum(xs)
    count = len(xs)
    mean = total / count if count else 0.0
    return {
        "sum": total,
        "mean": mean,
        "count": count,
        "min": min(xs) if xs else 0.0,
        "max": max(xs) if xs else 0.0,
    }


STEPS = {
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


def _provenance(in_path: str) -> str:
    """SHA-256 hex digest of the exact bytes of in_path."""
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lh09_series_build step runner")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    fn = STEPS[args.step]
    data = fn(prev)
    artifact = {
        "step": args.step,
        "data": data,
        "provenance": _provenance(args.in_path),
    }
    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(artifact, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
