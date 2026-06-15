"""Gold reference for long_horizon/lh06_matrix_ladder — a 12-step provenance chain.

Each step reads the JSON artifact from the previous step, applies its transform,
and writes a JSON artifact containing the result and a SHA-256 provenance hash of
the consumed file.

Steps:
  1  parse         — cast each int to float
  2  add_const     — add 5.0 to each element
  3  mod           — apply % 7 to each element
  4  scale_by_index— multiply element i by i (0-based)
  5  cumsum        — running cumulative sum
  6  prefix_max    — running maximum
  7  diffs         — consecutive differences (length n-1)
  8  abs           — absolute value of each element
  9  filter_gt_mean— keep elements strictly > mean
  10 sort_asc      — sort ascending
  11 dedupe        — remove duplicates preserving first-occurrence order
  12 aggregate     — compute total, mean, count, min, max
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import accumulate


# --------------------------------------------------------------------------- #
# Step implementations
# --------------------------------------------------------------------------- #

def step1_parse(prev: dict) -> list:
    """Cast each value in ``values`` to float."""
    return [float(v) for v in prev["values"]]


def step2_add_const(prev: dict) -> list:
    """Add 5.0 to every element."""
    return [v + 5.0 for v in prev["data"]]


def step3_mod(prev: dict) -> list:
    """Apply Python's % 7 to every element."""
    return [v % 7 for v in prev["data"]]


def step4_scale_by_index(prev: dict) -> list:
    """Multiply element at position i by i (0-based)."""
    return [v * i for i, v in enumerate(prev["data"])]


def step5_cumsum(prev: dict) -> list:
    """Running cumulative sum left-to-right."""
    return list(accumulate(prev["data"]))


def step6_prefix_max(prev: dict) -> list:
    """Running maximum left-to-right."""
    result = []
    running_max = float("-inf")
    for v in prev["data"]:
        running_max = max(running_max, v)
        result.append(running_max)
    return result


def step7_diffs(prev: dict) -> list:
    """Consecutive differences: data[i+1] - data[i]. Length is n-1."""
    xs = prev["data"]
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def step8_abs(prev: dict) -> list:
    """Absolute value of every element."""
    return [abs(v) for v in prev["data"]]


def step9_filter_gt_mean(prev: dict) -> list:
    """Keep only elements strictly greater than the arithmetic mean."""
    xs = prev["data"]
    if not xs:
        return []
    mean = sum(xs) / len(xs)
    return [v for v in xs if v > mean]


def step10_sort_asc(prev: dict) -> list:
    """Sort elements in ascending order."""
    return sorted(prev["data"])


def step11_dedupe(prev: dict) -> list:
    """Remove duplicate values preserving order of first occurrence."""
    seen: set = set()
    result = []
    for v in prev["data"]:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def step12_aggregate(prev: dict) -> dict:
    """Compute total, mean, count, min, max of the list."""
    xs = prev["data"]
    count = len(xs)
    total = float(sum(xs))
    mean = total / count if count else 0.0
    minimum = float(min(xs)) if xs else None
    maximum = float(max(xs)) if xs else None
    return {
        "total": total,
        "mean": mean,
        "count": count,
        "min": minimum,
        "max": maximum,
    }


# --------------------------------------------------------------------------- #
# Dispatch table
# --------------------------------------------------------------------------- #
STEPS = {
    1: step1_parse,
    2: step2_add_const,
    3: step3_mod,
    4: step4_scale_by_index,
    5: step5_cumsum,
    6: step6_prefix_max,
    7: step7_diffs,
    8: step8_abs,
    9: step9_filter_gt_mean,
    10: step10_sort_asc,
    11: step11_dedupe,
    12: step12_aggregate,
}


def run_step(step: int, prev: dict):
    """Dispatch to the transform function for ``step``."""
    if step not in STEPS:
        raise ValueError(f"Unknown step: {step}")
    return STEPS[step](prev)


def _provenance(in_path: str) -> str:
    """SHA-256 hex digest of the exact bytes in the consumed file."""
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lh06_matrix_ladder step runner")
    parser.add_argument("--step", type=int, required=True, help="Step number 1-12")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON artifact path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON artifact path")
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = run_step(args.step, prev)
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
