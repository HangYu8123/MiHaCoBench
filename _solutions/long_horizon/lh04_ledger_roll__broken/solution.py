"""Deliberately-broken reference for long_horizon/lh04_ledger_roll.

Planted defect: step 2 (cumsum) forgets to include the first element — it starts
accumulation from the second element, making the output list one element short and
all cumulative values wrong.  Steps 3-8 cascade incorrectly.  Step 1 (parse) stays
correct, demonstrating partial credit + cascade.  MUST fail the grader.
"""
from __future__ import annotations

import argparse
import hashlib
import json


def step1_parse(prev: dict) -> list:
    """Cast each value in ``values`` to float."""
    return [float(v) for v in prev["values"]]


def step2_cumsum(prev: dict) -> list:
    """BUG: skips the first element, starting accumulation from index 1."""
    xs = prev["data"]
    # Bug: start from index 1 instead of index 0, so result is len-1 long
    out, total = [], 0.0
    for v in xs[1:]:   # <-- planted defect: skips xs[0]
        total += v
        out.append(total)
    return out


def step3_prefix_min(prev: dict) -> list:
    """Running minimum."""
    xs = prev["data"]
    out, cur_min = [], float("inf")
    for v in xs:
        cur_min = min(cur_min, v)
        out.append(cur_min)
    return out


def step4_diffs(prev: dict) -> list:
    """Consecutive differences."""
    xs = prev["data"]
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def step5_abs(prev: dict) -> list:
    """Element-wise absolute value."""
    return [abs(v) for v in prev["data"]]


def step6_sort_asc(prev: dict) -> list:
    """Sort ascending."""
    return sorted(prev["data"])


def step7_dedupe(prev: dict) -> list:
    """Remove duplicates while preserving order."""
    seen: set = set()
    out: list = []
    for v in prev["data"]:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def step8_aggregate(prev: dict) -> dict:
    """Aggregate: sum, mean, count, min, max."""
    xs = prev["data"]
    n = len(xs)
    return {
        "sum": float(sum(xs)),
        "mean": float(sum(xs) / n) if n else 0.0,
        "count": n,
        "min": float(min(xs)),
        "max": float(max(xs)),
    }


STEPS = {
    1: step1_parse,
    2: step2_cumsum,
    3: step3_prefix_min,
    4: step4_diffs,
    5: step5_abs,
    6: step6_sort_asc,
    7: step7_dedupe,
    8: step8_aggregate,
}


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lh04_ledger_roll step runner")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    if args.step not in STEPS:
        raise ValueError(f"Unknown step: {args.step}")

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = STEPS[args.step](prev)
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
