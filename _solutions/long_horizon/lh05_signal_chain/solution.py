"""Gold reference for long_horizon/lh05_signal_chain — a 10-step signal processing chain.

CLI: python solution.py --step <K> --in <prev_json> --out <out_json>

Each step reads the JSON artifact produced by the previous step (or the raw
input.json for step 1) and writes:
  {"step": K, "data": <result>, "provenance": <sha256 of the --in file bytes>}
"""
from __future__ import annotations

import argparse
import hashlib
import json


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step1_parse_float(prev: dict) -> list:
    """Cast every element of ``values`` to float."""
    return [float(v) for v in prev["values"]]


def step2_normalize_minmax(prev: dict) -> list:
    """Min-max normalise to [0, 1]; guard against min == max (all-zero output)."""
    xs = list(prev["data"])
    mn = min(xs)
    mx = max(xs)
    if mx == mn:
        return [0.0] * len(xs)
    return [(v - mn) / (mx - mn) for v in xs]


def step3_scale(prev: dict) -> list:
    """Multiply every element by 100."""
    return [v * 100.0 for v in prev["data"]]


def step4_round3(prev: dict) -> list:
    """Round each element to 3 decimal places."""
    return [round(v, 3) for v in prev["data"]]


def step5_moving_avg_3(prev: dict) -> list:
    """Sliding window mean of width 3; output length = len(data) - 2."""
    xs = list(prev["data"])
    return [(xs[i] + xs[i + 1] + xs[i + 2]) / 3.0 for i in range(len(xs) - 2)]


def step6_square(prev: dict) -> list:
    """Square each element."""
    return [v * v for v in prev["data"]]


def step7_prefix_max(prev: dict) -> list:
    """Running maximum: result[i] = max(data[0..i])."""
    xs = list(prev["data"])
    result = []
    cur_max = None
    for v in xs:
        if cur_max is None or v > cur_max:
            cur_max = v
        result.append(cur_max)
    return result


def step8_diffs(prev: dict) -> list:
    """Consecutive differences: result[i] = data[i+1] - data[i]."""
    xs = list(prev["data"])
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def step9_sort_desc(prev: dict) -> list:
    """Sort descending."""
    return sorted(prev["data"], reverse=True)


def step10_aggregate(prev: dict) -> dict:
    """Summary statistics: sum, mean, min, max, count."""
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _provenance(in_path: str) -> str:
    """SHA-256 hex digest of the exact bytes of the consumed file."""
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lh05_signal_chain step runner")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    fn = STEPS.get(args.step)
    if fn is None:
        raise ValueError(f"unknown step {args.step}; must be 1-10")
    data = fn(prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
