#!/usr/bin/env python3
"""Grade the fast-vs-skill validation subset (16 tasks) per arm, cleanly.

Unlike grade_all.py (which grades all 79 and overwrites eval_<arm>_full.json),
this grades ONLY the 16 subset tasks for each arm via
``run_benchmark.py --candidate-root cand_<arm> --task <id>``, so it:
  * never clobbers the existing eval_fast_full.json / eval_naive_full.json baselines,
  * does minimal grading work (16 tasks x N arms), and
  * emits a side-by-side fast-vs-skill comparison.

Outputs (under experiment_mihaco/results/):
  eval_<arm>_subset.json         per-arm, per-task scores + subset rollup
  VALIDATION_FAST_VS_SKILL.json  combined comparison
and prints a comparison table.

Usage:
    python3 experiment_mihaco/_grade_validate.py            # arms = fast skill
    python3 experiment_mihaco/_grade_validate.py fast skill
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
EXP = BENCH / "experiment_mihaco"
RES = EXP / "results"
RESULTS_JSON = BENCH / "results.json"

SUBSET = [
    ("easy", "e01_csv_pulse"),
    ("easy", "e06_semver_order"),
    ("algorithmic", "a04_edit_distance"),
    ("algorithmic", "a08_cooldown_profit"),
    ("complex", "c01_job_queue_sqla"),
    ("complex", "c09_reactive_engine"),
    ("data_analysis", "d05_experiment_anova"),
    ("data_analysis", "d07_paired_design"),
    ("long_horizon", "lh12_budget_forecast"),
    ("ml", "m03_clustering"),
    ("compositional", "cb02_workflow_dag"),
    ("compositional", "cb08_cursor_paginate"),
    ("competitive", "cp05_kth_subarray_sum"),
    ("debug", "dbg02_resolve_order"),
    ("debug", "dbg07_token_bucket"),
    ("swe_bench", "swe08_money_rounding"),
]


def grade_one(arm: str, cat: str, tid: str) -> dict:
    root = EXP / f"cand_{arm}"
    cand_dir = root / cat / tid
    if RESULTS_JSON.exists():
        RESULTS_JSON.unlink()
    proc = subprocess.run(
        [sys.executable, "run_benchmark.py", "--candidate-root", str(root), "--task", tid],
        cwd=str(BENCH), capture_output=True, text=True,
    )
    entry = None
    if RESULTS_JSON.exists():
        data = json.loads(RESULTS_JSON.read_text())
        for e in data.get("tasks", []):
            if e.get("id") == tid:
                entry = e
                break
    pys = sorted(p.name for p in cand_dir.glob("*.py")) if cand_dir.is_dir() else []
    if entry is None:
        return {
            "cat": cat, "id": tid, "weight": None, "passed": 0, "total": 0,
            "partial": 0.0, "strict": 0,
            "status": "MISSING_DIR" if not cand_dir.is_dir() else ("NO_PY" if not pys else "NO_RESULT"),
            "files": pys, "stderr_tail": proc.stderr[-400:],
        }
    return {
        "cat": cat, "id": tid, "weight": entry.get("weight"),
        "passed": entry.get("passed"), "total": entry.get("total"),
        "partial": entry.get("partial"), "strict": entry.get("strict"),
        "status": "graded", "files": pys,
    }


def rollup(rows: list[dict]) -> dict:
    wsum = sum((r["weight"] or 0.0) for r in rows)
    wpart = sum((r["weight"] or 0.0) * (r["partial"] or 0.0) for r in rows)
    strict_n = sum(1 for r in rows if r.get("strict") == 1)
    return {
        "n": len(rows),
        "strict_total": f"{strict_n}/{len(rows)}",
        "strict_n": strict_n,
        "weighted_partial": round(wpart / wsum, 4) if wsum else 0.0,
        "weight_sum": wsum,
    }


def main(arms: list[str]) -> int:
    RES.mkdir(parents=True, exist_ok=True)
    per_arm = {}
    for arm in arms:
        rows = []
        print(f"\n===== grading arm: {arm} ({len(SUBSET)} tasks) =====")
        for cat, tid in SUBSET:
            r = grade_one(arm, cat, tid)
            rows.append(r)
            flag = "" if r["status"] == "graded" else f"  [{r['status']}]"
            print(f"  {arm:5s} {cat:13s} {tid:28s} "
                  f"partial={r['partial']!s:5} strict={r['strict']}{flag}")
        roll = rollup(rows)
        per_arm[arm] = {"rollup": roll, "tasks": rows}
        (RES / f"eval_{arm}_subset.json").write_text(
            json.dumps(per_arm[arm], indent=2, default=str))
        print(f"  -> {arm}: strict {roll['strict_total']}  weighted_partial {roll['weighted_partial']}")

    comp = {"subset_size": len(SUBSET), "arms": arms, "per_arm_rollup": {a: per_arm[a]["rollup"] for a in arms}}
    # per-task side-by-side
    table = []
    for i, (cat, tid) in enumerate(SUBSET):
        row = {"cat": cat, "id": tid}
        for arm in arms:
            t = per_arm[arm]["tasks"][i]
            row[arm] = {"partial": t["partial"], "strict": t["strict"], "status": t["status"]}
        table.append(row)
    comp["per_task"] = table
    (RES / "VALIDATION_FAST_VS_SKILL.json").write_text(json.dumps(comp, indent=2, default=str))

    # printed comparison
    print("\n================ FAST vs SKILL (16-task subset) ================")
    hdr = f"{'category':13s} {'task':28s} " + " ".join(f"{a:>16s}" for a in arms)
    print(hdr)
    for i, (cat, tid) in enumerate(SUBSET):
        cells = []
        for arm in arms:
            t = per_arm[arm]["tasks"][i]
            mark = "OK " if t["strict"] == 1 else "   "
            cells.append(f"{mark}p={t['partial']!s:>5}")
        print(f"{cat:13s} {tid:28s} " + " ".join(f"{c:>16s}" for c in cells))
    print("-" * 78)
    for arm in arms:
        r = per_arm[arm]["rollup"]
        print(f"  {arm:6s}  strict {r['strict_total']:8s}  weighted_partial {r['weighted_partial']}")
    print("wrote", RES / "VALIDATION_FAST_VS_SKILL.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["fast", "skill"]))
