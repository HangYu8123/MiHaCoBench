"""Deliberately-broken reference for long_horizon/lh03_vector_forge.

Planted defect: step 4 keeps elements LESS THAN the mean (inverted filter)
instead of greater than — the opposite of the specified contract. Steps 1-3 are
correct; steps 4-6 are all wrong, demonstrating cascade. MUST fail the grader.
"""
from __future__ import annotations

import argparse
import hashlib
import json


def run_step(step: int, prev: dict):
    if step == 1:
        return [float(v) for v in prev["values"]]
    if step == 2:
        return [v * 2.0 for v in prev["data"]]
    if step == 3:
        return [v + 3.0 for v in prev["data"]]
    if step == 4:
        xs = list(prev["data"])
        if not xs:
            return []
        mean = sum(xs) / len(xs)
        # BUG: keeps elements < mean instead of > mean (inverted filter)
        return [v for v in xs if v < mean]
    if step == 5:
        return sorted(prev["data"], reverse=True)
    if step == 6:
        xs = list(prev["data"])
        count = len(xs)
        total = sum(xs)
        return {
            "sum": float(total),
            "mean": float(total / count) if count else 0.0,
            "min": float(min(xs)) if xs else 0.0,
            "max": float(max(xs)) if xs else 0.0,
            "count": count,
        }
    raise ValueError(f"Unknown step {step}")


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
    prov = _provenance(args.in_path)
    with open(args.out_path, "w", encoding="utf-8") as handle:
        json.dump({"step": args.step, "data": data, "provenance": prov}, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
