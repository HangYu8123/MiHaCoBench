"""Gold reference for long_horizon/lh13_quota_ledger — a 10-step budget ledger.

CLI: python solution.py --step <K> --in <prev_json> --out <out_json>

Unlike a stateless transform chain, this pipeline threads a GLOBAL INVARIANT: a
fixed budget set at step 1 is drawn down across steps 2..9 as queued requests are
granted against the RUNNING remainder. The only way to stay correct is to carry
``remaining`` and ``committed`` forward from the previous step — a step that
re-derives the budget locally silently overdraws.

Each step writes:
  {"step": K, "data": <state-or-summary>, "provenance": <sha256 of the --in bytes>}
"""
from __future__ import annotations

import argparse
import hashlib
import json

_EPS = 1e-9


def step1_init(prev: dict) -> dict:
    """Load the budget and the request queue; nothing is committed yet."""
    budget = float(prev["budget"])
    queue = [{"id": r["id"], "amount": float(r["amount"])} for r in prev["requests"]]
    return {"budget": budget, "remaining": budget, "queue": queue, "committed": []}


def _process(prev: dict) -> dict:
    """Grant the next queued request against the RUNNING remaining (cumulative).

    Carries forward the budget, the decremented remaining, the shortened queue,
    and the appended commitment list from the previous step's state.
    """
    state = prev["data"]
    budget = state["budget"]
    remaining = state["remaining"]
    queue = list(state["queue"])
    committed = [dict(c) for c in state["committed"]]
    if queue:
        req = queue.pop(0)
        amount = float(req["amount"])
        granted = amount if amount <= remaining else remaining  # cap at REMAINING
        remaining = remaining - granted
        committed.append({"id": req["id"], "requested": amount, "granted": granted})
    return {"budget": budget, "remaining": remaining, "queue": queue, "committed": committed}


def step10_reconcile(prev: dict) -> dict:
    """Summarise the ledger and check the conservation invariant."""
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
    2: _process,
    3: _process,
    4: _process,
    5: _process,
    6: _process,
    7: _process,
    8: _process,
    9: _process,
    10: step10_reconcile,
}


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lh13_quota_ledger step runner")
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
