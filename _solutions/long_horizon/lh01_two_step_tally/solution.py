"""Gold reference for long_horizon/lh01_two_step_tally — a 2-step provenance chain."""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import accumulate


def step1_scale_and_shift(prev: dict) -> list:
    """v -> v*2 + 1 over the input ``values`` list."""
    return [v * 2 + 1 for v in prev["values"]]


def step2_cumulative_stats(prev: dict) -> dict:
    """Cumulative sums + total/mean/count over step 1's list."""
    xs = list(prev["data"])  # --in is step 1's full artifact; the list is under "data"
    cumsum = list(accumulate(xs))
    return {
        "cumsum": cumsum,
        "total": sum(xs),
        "mean": (sum(xs) / len(xs)) if xs else 0.0,
        "count": len(xs),
    }


STEPS = {1: step1_scale_and_shift, 2: step2_cumulative_stats}


def run_step(step: int, prev):
    """Dispatch to the transform for ``step``."""
    return STEPS[step](prev)


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
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
