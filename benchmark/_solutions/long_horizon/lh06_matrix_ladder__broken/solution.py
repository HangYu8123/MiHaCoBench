"""Deliberately-broken reference for long_horizon/lh06_matrix_ladder.

Planted defect: step 4 (scale_by_index) multiplies element i by (i+1) instead of i
(1-based index instead of the required 0-based index). This makes step 4's output
wrong, which cascades through steps 5-12. Step 1-3 remain correct, so the grader
awards partial credit for the early correct steps and fails on step 4 onwards.

MUST fail the grader on at least one test (step 4 and all downstream steps).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import accumulate


def run_step(step: int, prev: dict):
    """Dispatch to the transform for ``step``."""
    if step == 1:
        return [float(v) for v in prev["values"]]

    if step == 2:
        return [v + 5.0 for v in prev["data"]]

    if step == 3:
        return [v % 7 for v in prev["data"]]

    if step == 4:
        # BUG: uses 1-based index (i+1) instead of 0-based (i)
        return [v * (i + 1) for i, v in enumerate(prev["data"])]

    if step == 5:
        return list(accumulate(prev["data"]))

    if step == 6:
        result = []
        running_max = float("-inf")
        for v in prev["data"]:
            running_max = max(running_max, v)
            result.append(running_max)
        return result

    if step == 7:
        xs = prev["data"]
        return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]

    if step == 8:
        return [abs(v) for v in prev["data"]]

    if step == 9:
        xs = prev["data"]
        if not xs:
            return []
        mean = sum(xs) / len(xs)
        return [v for v in xs if v > mean]

    if step == 10:
        return sorted(prev["data"])

    if step == 11:
        seen: set = set()
        result = []
        for v in prev["data"]:
            if v not in seen:
                seen.add(v)
                result.append(v)
        return result

    if step == 12:
        xs = prev["data"]
        count = len(xs)
        total = float(sum(xs))
        mean = total / count if count else 0.0
        return {
            "total": total,
            "mean": mean,
            "count": count,
            "min": float(min(xs)) if xs else None,
            "max": float(max(xs)) if xs else None,
        }

    raise ValueError(f"Unknown step: {step}")


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
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
