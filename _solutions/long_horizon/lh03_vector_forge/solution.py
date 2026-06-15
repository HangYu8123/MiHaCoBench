"""Gold reference for long_horizon/lh03_vector_forge — a 6-step vector pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json


def step1_parse(prev: dict) -> list:
    """Cast each element of ``values`` to float (identity — no scaling)."""
    return [float(v) for v in prev["values"]]


def step2_double(prev: dict) -> list:
    """Multiply each element by 2."""
    return [v * 2.0 for v in prev["data"]]


def step3_add_const(prev: dict) -> list:
    """Add 3 to each element."""
    return [v + 3.0 for v in prev["data"]]


def step4_filter_gt_mean(prev: dict) -> list:
    """Keep only elements strictly greater than the arithmetic mean."""
    xs = list(prev["data"])
    if not xs:
        return []
    mean = sum(xs) / len(xs)
    return [v for v in xs if v > mean]


def step5_sort_desc(prev: dict) -> list:
    """Sort elements in descending order."""
    return sorted(prev["data"], reverse=True)


def step6_aggregate(prev: dict) -> dict:
    """Compute sum, mean, min, max, count over the list."""
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


STEPS = {
    1: step1_parse,
    2: step2_double,
    3: step3_add_const,
    4: step4_filter_gt_mean,
    5: step5_sort_desc,
    6: step6_aggregate,
}


def run_step(step: int, prev: dict):
    """Dispatch to the transform for the given step number."""
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
