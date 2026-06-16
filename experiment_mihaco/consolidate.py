#!/usr/bin/env python3
"""Consolidate full-run results into results/consolidated_full.json.

Picks up whichever eval_<arm>_full.json files exist (so it works after just
naive+fast, and again later once general is added) plus tokens_full.json.

Usage:  python3 experiment_mihaco/consolidate.py
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
EXP = BENCH / "experiment_mihaco"
RES = EXP / "results"
ARMS = ["naive", "fast", "general"]


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def main() -> int:
    tokens = load(RES / "tokens_full.json") or {}
    tok_arms = tokens.get("arms", {})
    out = {
        "experiment": "HarnessFlow x MiHaCoBench — FULL 35-task suite",
        "orchestrator_model": "claude-opus-4-8",
        "subagent_model": "claude-sonnet-4-6",
        "note": "naive+fast generated/graded in this run; the 6 *01 pilot tasks are reused. "
                "general arm runnable later via RUNBOOK.md; this file regenerates with it included.",
        "arms": {},
    }
    naive_tok = (tok_arms.get("naive") or {}).get("total_tokens")
    for arm in ARMS:
        ev = load(RES / f"eval_{arm}_full.json")
        if not ev or "tasks" not in ev:
            continue
        per = {r["id"]: {"passed": r["passed"], "total": r["total"],
                         "partial": r["partial"], "strict": r["strict"],
                         "weight": r.get("weight")} for r in ev["tasks"]}
        t = tok_arms.get(arm, {})
        rec = {
            "strict_total": ev.get("strict_total"),
            "weighted_partial": ev.get("weighted_partial"),
            "n_tasks": len(ev["tasks"]),
            "category_totals": ev.get("category_totals"),
            "tokens": {
                "subagents": t.get("count"),
                "total_tokens": t.get("total_tokens"),
                "output_tokens": t.get("output_tokens"),
                "cache_read_input_tokens": t.get("cache_read_input_tokens"),
                "x_naive": round(t.get("total_tokens") / naive_tok, 3) if (naive_tok and t.get("total_tokens")) else None,
            },
            "per_task": per,
        }
        out["arms"][arm] = rec

    out["grand_total_subagent_tokens"] = tokens.get("grand_total_tokens")
    (RES / "consolidated_full.json").write_text(json.dumps(out, indent=2, default=str))

    # console summary
    print(f"{'arm':9}{'strict':>10}{'weighted':>11}{'subagents':>11}{'tokens':>14}{'x_naive':>9}")
    for arm in ARMS:
        a = out["arms"].get(arm)
        if not a:
            continue
        tk = a["tokens"]
        print(f"{arm:9}{str(a['strict_total']):>10}{a['weighted_partial']:>11}"
              f"{str(tk['subagents']):>11}{(tk['total_tokens'] or 0):>14,}{str(tk['x_naive']):>9}")
    print(f"\nwrote {RES/'consolidated_full.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
