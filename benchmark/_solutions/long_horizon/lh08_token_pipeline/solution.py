"""Gold reference for long_horizon/lh08_token_pipeline — a 16-step provenance chain.

Each invocation handles exactly one step of the numeric token pipeline and writes
its artifact (including provenance SHA-256) to the specified output file.
"""
from __future__ import annotations

import argparse
import hashlib
import json


# --------------------------------------------------------------------------- #
# Step implementations
# --------------------------------------------------------------------------- #

def step1_parse(prev: dict) -> list:
    """Cast raw integer values to floats."""
    return [float(v) for v in prev["values"]]


def step2_add_const(prev: dict) -> list:
    """Add 1 to every element."""
    return [v + 1.0 for v in prev["data"]]


def step3_double(prev: dict) -> list:
    """Multiply every element by 2."""
    return [v * 2.0 for v in prev["data"]]


def step4_mod(prev: dict) -> list:
    """Apply modulo 5 to every element."""
    return [v % 5 for v in prev["data"]]


def step5_scale_by_index(prev: dict) -> list:
    """Multiply each element by its zero-based index."""
    return [v * i for i, v in enumerate(prev["data"])]


def step6_cumsum(prev: dict) -> list:
    """Replace list with cumulative sums."""
    result = []
    total = 0.0
    for v in prev["data"]:
        total += v
        result.append(total)
    return result


def step7_prefix_max(prev: dict) -> list:
    """Replace list with running prefix maximum."""
    result = []
    current_max = float("-inf")
    for v in prev["data"]:
        current_max = max(current_max, v)
        result.append(current_max)
    return result


def step8_diffs(prev: dict) -> list:
    """Consecutive differences; output length = input length - 1."""
    data = prev["data"]
    return [data[i] - data[i - 1] for i in range(1, len(data))]


def step9_abs(prev: dict) -> list:
    """Apply abs() to every element."""
    return [abs(v) for v in prev["data"]]


def step10_square(prev: dict) -> list:
    """Square every element."""
    return [v * v for v in prev["data"]]


def step11_normalize_minmax(prev: dict) -> list:
    """Min-max normalisation: (x - min) / (max - min). All-equal => all zeros."""
    data = prev["data"]
    mn = min(data)
    mx = max(data)
    if mx == mn:
        return [0.0] * len(data)
    return [(v - mn) / (mx - mn) for v in data]


def step12_scale(prev: dict) -> list:
    """Multiply every element by 10."""
    return [v * 10.0 for v in prev["data"]]


def step13_round3(prev: dict) -> list:
    """Round every element to 3 decimal places."""
    return [round(v, 3) for v in prev["data"]]


def step14_sort_asc(prev: dict) -> list:
    """Sort the list ascending."""
    return sorted(prev["data"])


def step15_dedupe(prev: dict) -> list:
    """Remove consecutive duplicate values (preserves order, keeps first)."""
    result = []
    for v in prev["data"]:
        if not result or result[-1] != v:
            result.append(v)
    return result


def step16_aggregate(prev: dict) -> dict:
    """Compute summary statistics over the deduplicated list."""
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


# --------------------------------------------------------------------------- #
# Provenance helper
# --------------------------------------------------------------------------- #

def _provenance(in_path: str) -> str:
    """SHA-256 of the raw bytes of the input file."""
    with open(in_path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One step of the 16-step token pipeline.")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    with open(args.in_path, encoding="utf-8") as fh:
        prev = json.load(fh)

    if args.step not in STEPS:
        raise ValueError(f"Unknown step: {args.step}")

    data = STEPS[args.step](prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}

    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
