"""Deliberately-broken reference for long_horizon/lh01_two_step_tally.

Planted defect: step 2 divides by (count - 1) instead of count, so `mean` (and the
cumulative test) are wrong. Step 1 stays correct, demonstrating partial credit +
cascade. MUST fail the grader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import accumulate


def run_step(step: int, prev):
    if step == 1:
        return [v * 2 + 1 for v in prev["values"]]
    xs = list(prev["data"])
    return {
        "cumsum": list(accumulate(xs)),
        "total": sum(xs),
        "mean": (sum(xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0,  # BUG: ddof-style off-by-one
        "count": len(xs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)
    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = run_step(args.step, prev)
    prov = hashlib.sha256(open(args.in_path, "rb").read()).hexdigest()
    with open(args.out_path, "w", encoding="utf-8") as handle:
        json.dump({"step": args.step, "data": data, "provenance": prov}, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
