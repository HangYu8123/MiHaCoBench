#!/usr/bin/env python3
"""Batch progress logger + next-batch picker for the MiHaCoBench full run.

Single source of truth = the candidate dirs on disk. Each call:
  1. scans cand_{naive,fast,skill}/<cat>/<id>/ for a .py solution,
  2. (re)writes results/BATCH_PROGRESS.md (human log) + results/batch_state.json
     (machine state, with an append-only history of progress snapshots),
  3. prints the NEXT batch of pending (arm,task) jobs as JSON for the generator.

Usage:
    python3 experiment_mihaco/_batch_log.py [k_tasks=8] [arm ...]   # default arms: fast skill
The printed line `NEXT_BATCH_JOBS=[...]` is fed to _gen_batch.js via the Workflow
tool's args: Workflow({scriptPath: ".../_gen_batch.js"}, args={"jobs": <that list>}).
"""
from __future__ import annotations
import glob, json, os, sys
from collections import defaultdict
from datetime import datetime, timezone

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(BENCH, "experiment_mihaco")
RES = os.path.join(EXP, "results")
STATE = os.path.join(RES, "batch_state.json")
MD = os.path.join(RES, "BATCH_PROGRESS.md")
ARMS_ALL = ["naive", "fast", "skill"]


def load_tasks():
    out = []
    for m in sorted(glob.glob(os.path.join(BENCH, "tasks/*/*/task.json"))):
        d = json.loads(open(m).read())
        cat, tid = d["category"], d["id"]
        mode = "debug" if cat in ("debug", "swe_bench") else "code"
        out.append({"cat": cat, "id": tid, "mode": mode, "weight": d.get("weight")})
    return out


def interleave(tasks):
    bycat = defaultdict(list)
    for t in tasks:
        bycat[t["cat"]].append(t)
    cats = sorted(bycat)
    order, i = [], 0
    while any(i < len(bycat[c]) for c in cats):
        for c in cats:
            if i < len(bycat[c]):
                order.append(bycat[c][i])
        i += 1
    return order


def done(arm, t):
    d = os.path.join(EXP, f"cand_{arm}", t["cat"], t["id"])
    return os.path.isdir(d) and any(f.endswith(".py") for f in os.listdir(d))


def main(argv):
    k = int(argv[0]) if argv and argv[0].isdigit() else 8
    req_arms = [a for a in argv if a in ARMS_ALL] or ["fast", "skill"]
    tasks = load_tasks()
    order = interleave(tasks)
    status = {a: {t["id"]: done(a, t) for t in tasks} for a in ARMS_ALL}

    counts = {a: sum(status[a].values()) for a in ARMS_ALL}
    n = len(tasks)

    # next batch: next k tasks (interleaved) with any requested arm pending
    next_jobs, picked = [], 0
    for t in order:
        pend = [a for a in req_arms if not status[a][t["id"]]]
        if not pend:
            continue
        for a in pend:
            next_jobs.append({"arm": a, "cat": t["cat"], "id": t["id"], "mode": t["mode"]})
        picked += 1
        if picked >= k:
            break

    # history (append snapshot only when counts change)
    hist = []
    if os.path.exists(STATE):
        try:
            hist = json.loads(open(STATE).read()).get("history", [])
        except Exception:
            hist = []
    snap = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "naive": counts["naive"], "fast": counts["fast"], "skill": counts["skill"]}
    if not hist or (hist[-1]["naive"], hist[-1]["fast"], hist[-1]["skill"]) != (snap["naive"], snap["fast"], snap["skill"]):
        hist.append(snap)

    state = {
        "n_tasks": n, "counts": counts, "req_arms": req_arms,
        "pending": {a: [t["id"] for t in tasks if not status[a][t["id"]]] for a in ARMS_ALL},
        "history": hist,
        "per_task": [{"id": t["id"], "cat": t["cat"], "mode": t["mode"],
                      **{a: bool(status[a][t["id"]]) for a in ARMS_ALL}} for t in tasks],
    }
    os.makedirs(RES, exist_ok=True)
    open(STATE, "w").write(json.dumps(state, indent=2))

    # per-category rollup
    cats = sorted({t["cat"] for t in tasks})
    lines = ["# MiHaCoBench full run — batch progress log", "",
             f"_updated: {snap['ts']}_  ·  arms tracked: naive, fast, skill", "",
             "## Totals", "",
             "| arm | done / 79 |", "|---|---|"]
    for a in ARMS_ALL:
        lines.append(f"| {a} | {counts[a]} / {n} |")
    lines += ["", "## Per-category (done/total)", "",
              "| category | total | naive | fast | skill |", "|---|--:|--:|--:|--:|"]
    for c in cats:
        ct = [t for t in tasks if t["cat"] == c]
        row = [c, str(len(ct))] + [str(sum(1 for t in ct if status[a][t["id"]])) for a in ARMS_ALL]
        lines.append("| " + " | ".join(row) + " |")
    pend_fast = state["pending"]["fast"]; pend_skill = state["pending"]["skill"]
    lines += ["", "## Pending", "",
              f"- fast pending ({len(pend_fast)}): {', '.join(pend_fast) or 'none'}",
              f"- skill pending ({len(pend_skill)}): {', '.join(pend_skill) or 'none'}",
              "", "## Progress history", "", "| timestamp (UTC) | naive | fast | skill |", "|---|--:|--:|--:|"]
    for h in hist:
        lines.append(f"| {h['ts']} | {h['naive']} | {h['fast']} | {h['skill']} |")
    open(MD, "w").write("\n".join(lines) + "\n")

    print(f"counts: naive={counts['naive']} fast={counts['fast']} skill={counts['skill']} (/{n})")
    print(f"pending fast={len(pend_fast)} skill={len(pend_skill)}; next batch picks {picked} task(s) -> {len(next_jobs)} jobs")
    print(f"log: {MD}")
    print("NEXT_BATCH_JOBS=" + json.dumps(next_jobs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
