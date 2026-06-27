"""Broken reference for long_horizon/lh13_quota_ledger.

PLANTED DEFECT (the cumulative-state trap): in each processing step the grant and
the new ``remaining`` are computed from the FULL budget rather than from the
running remainder carried in from the previous step. Each step in isolation looks
fine (it reads prev["data"], pops the next request, records a commitment), but it
ignores everything already committed, so it grants far more than the budget allows
and the final conservation check (total_granted + remaining == budget) fails.

step1 and step10 are identical to the gold; only the per-request processing
re-derives the budget locally instead of threading the remainder.
"""
from __future__ import annotations

import argparse
import hashlib
import json

_EPS = 1e-9


def step1_init(prev: dict) -> dict:
    budget = float(prev["budget"])
    queue = [{"id": r["id"], "amount": float(r["amount"])} for r in prev["requests"]]
    return {"budget": budget, "remaining": budget, "queue": queue, "committed": []}


def _process_broken(prev: dict) -> dict:
    state = prev["data"]
    budget = state["budget"]
    queue = list(state["queue"])
    committed = [dict(c) for c in state["committed"]]
    if queue:
        req = queue.pop(0)
        amount = float(req["amount"])
        granted = amount if amount <= budget else budget   # BUG: caps at full budget
        remaining = budget - granted                        # BUG: ignores prior commitments
        committed.append({"id": req["id"], "requested": amount, "granted": granted})
    else:
        remaining = state["remaining"]
    return {"budget": budget, "remaining": remaining, "queue": queue, "committed": committed}


def step10_reconcile(prev: dict) -> dict:
    state = prev["data"]
    budget = state["budget"]
    remaining = state["remaining"]
    committed = state["committed"]
    total_granted = sum(c["granted"] for c in committed)
    fully = sum(1 for c in committed if c["granted"] >= c["requested"] - _EPS and c["granted"] > _EPS)
    partial = sum(1 for c in committed if _EPS < c["granted"] < c["requested"] - _EPS)
    rejected = sum(1 for c in committed if c["granted"] <= _EPS)
    return {
        "budget": budget,
        "total_granted": total_granted,
        "remaining": remaining,
        "utilization": (total_granted / budget) if budget else 0.0,
        "fully_granted": fully,
        "partial": partial,
        "rejected": rejected,
        "reconciled": abs(total_granted + remaining - budget) < _EPS,
    }


STEPS = {
    1: step1_init,
    2: _process_broken,
    3: _process_broken,
    4: _process_broken,
    5: _process_broken,
    6: _process_broken,
    7: _process_broken,
    8: _process_broken,
    9: _process_broken,
    10: step10_reconcile,
}


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lh13_quota_ledger step runner (broken)")
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
