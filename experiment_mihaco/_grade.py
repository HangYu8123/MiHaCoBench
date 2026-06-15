#!/usr/bin/env python3
"""Grade a candidate root against a fixed set of tasks, accumulating results.

Works around run_benchmark.py overwriting benchmark/results.json on every
``evaluate()`` call: we invoke the runner once per task (``--task <full_id>``),
read results.json immediately after each run, and accumulate into one per-arm
report so no task result is lost.

Usage:
    python3 experiment_mihaco/_grade.py --arm naive \
        --candidate-root experiment_mihaco/cand_naive \
        --out experiment_mihaco/results/eval_naive.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parents[1]
RESULTS_JSON = BENCH_ROOT / "results.json"

# One task per category (the pilot set), full ids for unambiguous --task match.
PILOT_TASKS = [
    ("easy", "e01_csv_pulse", 1),
    ("algorithmic", "a01_find_pair_indices", 2),
    ("data_analysis", "d01_ab_test_report", 3),
    ("ml", "m01_tabular_classification", 3),
    ("complex", "c01_job_queue_sqla", 5),
    ("long_horizon", "lh01_two_step_tally", 1),
]


def grade_one(candidate_root: Path, task_id: str) -> dict | None:
    """Run the benchmark for a single task and return its row from results.json."""
    if RESULTS_JSON.exists():
        RESULTS_JSON.unlink()
    proc = subprocess.run(
        [sys.executable, "run_benchmark.py",
         "--candidate-root", str(candidate_root), "--task", task_id],
        cwd=str(BENCH_ROOT), capture_output=True, text=True,
    )
    if not RESULTS_JSON.exists():
        return {"id": task_id, "error": "no results.json",
                "stdout_tail": proc.stdout[-800:], "stderr_tail": proc.stderr[-800:]}
    data = json.loads(RESULTS_JSON.read_text())
    rows = [r for r in data.get("tasks", []) if r["id"] == task_id]
    return rows[0] if rows else {"id": task_id, "error": "task row missing"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--candidate-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    root = args.candidate_root.resolve()
    rows: list[dict] = []
    cat_tot: dict[str, dict] = {}
    for cat, task_id, weight in PILOT_TASKS:
        row = grade_one(root, task_id)
        row.setdefault("category", cat)
        row.setdefault("weight", weight)
        rows.append(row)
        c = cat_tot.setdefault(cat, {"weight": 0.0, "weighted": 0.0, "strict": 0, "n": 0})
        partial = float(row.get("partial", 0.0) or 0.0)
        c["weight"] += weight
        c["weighted"] += weight * partial
        c["strict"] += int(row.get("strict", 0) or 0)
        c["n"] += 1
        passed = row.get("passed", "?")
        total = row.get("total", "?")
        print(f"  [{args.arm:8}] {cat:13} {task_id:26} "
              f"{passed}/{total} partial={partial:.3f} strict={row.get('strict', 0)} (w={weight})")

    tot_w = sum(c["weight"] for c in cat_tot.values())
    tot_ww = sum(c["weighted"] for c in cat_tot.values())
    tot_strict = sum(c["strict"] for c in cat_tot.values())
    tot_n = sum(c["n"] for c in cat_tot.values())
    weighted_partial = round(tot_ww / tot_w, 4) if tot_w else 0.0
    summary = {
        "arm": args.arm,
        "candidate_root": str(root),
        "tasks": rows,
        "category_totals": cat_tot,
        "strict_total": f"{tot_strict}/{tot_n}",
        "weighted_partial": weighted_partial,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2))
    print(f"  [{args.arm}] strict {tot_strict}/{tot_n}  weighted_partial={weighted_partial}  -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
