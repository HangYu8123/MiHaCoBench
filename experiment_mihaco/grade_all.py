#!/usr/bin/env python3
"""Grade candidate arms over the FULL 35-task MiHaCoBench suite, robustly.

Fixes the apparatus risks the Devil's-Advocate review flagged:
* H1 (results.json overwrite race): grade ONE arm at a time; copy
  ``results.json`` -> ``results/eval_<arm>_full.json`` immediately, guarded.
* H2 (_grade.py only graded 6 pilot tasks): this grades all 35 via
  ``run_benchmark.py --candidate-root``.
* H3 (missing dir == silent 0): a pre-grade pass records, per task, whether the
  candidate dir is MISSING / has NO_PY_FILES / has a COMPILE_ERROR, so a
  no-solution is distinguishable from a ran-but-failed. These are RECORDED, not
  fixed (candidate-side errors are logged for later fix tasks).

Usage:
    python3 experiment_mihaco/grade_all.py naive fast      # default
    python3 experiment_mihaco/grade_all.py general         # later
"""
from __future__ import annotations

import glob
import json
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
EXP = BENCH / "experiment_mihaco"
RES = EXP / "results"
RESULTS_JSON = BENCH / "results.json"


def all_tasks() -> list[tuple[str, str, dict]]:
    out = []
    for m in sorted(glob.glob(str(BENCH / "tasks/*/*/task.json"))):
        d = json.loads(Path(m).read_text())
        out.append((d["category"], d["id"], d))
    return out


def precheck(arm: str) -> list[dict]:
    """Per-task apparatus state for a candidate arm (does NOT fix anything)."""
    issues = []
    for cat, tid, _meta in all_tasks():
        d = EXP / f"cand_{arm}" / cat / tid
        if not d.is_dir():
            issues.append({"cat": cat, "id": tid, "kind": "MISSING_DIR", "detail": str(d)})
            continue
        pys = list(d.glob("*.py"))
        if not pys:
            issues.append({"cat": cat, "id": tid, "kind": "NO_PY_FILES", "detail": ""})
            continue
        for p in pys:
            try:
                py_compile.compile(str(p), doraise=True)
            except py_compile.PyCompileError as e:
                first = (str(e).splitlines() or [""])[0]
                issues.append({"cat": cat, "id": tid, "kind": "COMPILE_ERROR",
                               "detail": f"{p.name}: {first[:240]}"})
    return issues


def grade(arm: str) -> tuple[subprocess.CompletedProcess, Path]:
    root = EXP / f"cand_{arm}"
    if RESULTS_JSON.exists():
        RESULTS_JSON.unlink()
    proc = subprocess.run(
        [sys.executable, "run_benchmark.py", "--candidate-root", str(root)],
        cwd=str(BENCH), capture_output=True, text=True,
    )
    out = RES / f"eval_{arm}_full.json"
    if RESULTS_JSON.exists():
        shutil.copy(RESULTS_JSON, out)          # guarded copy BEFORE next arm runs
    else:
        out.write_text(json.dumps({"arm": arm, "error": "no results.json",
                                   "stdout_tail": proc.stdout[-2000:],
                                   "stderr_tail": proc.stderr[-2000:]}, indent=2))
    return proc, out


def main(arms: list[str]) -> int:
    RES.mkdir(parents=True, exist_ok=True)
    summary = {}
    for arm in arms:
        issues = precheck(arm)
        proc, out = grade(arm)
        data = json.loads(out.read_text()) if out.exists() else {}
        summary[arm] = {
            "eval_file": str(out),
            "strict_total": data.get("strict_total"),
            "weighted_partial": data.get("weighted_partial"),
            "apparatus_issue_count": len(issues),
            "apparatus_issues": issues,
        }
        print(f"\n========== [{arm}] strict={data.get('strict_total')} "
              f"weighted={data.get('weighted_partial')} "
              f"apparatus_issues={len(issues)} -> {out.name} ==========")
        print(proc.stdout[-3000:])
        if proc.stderr.strip():
            print("--- stderr tail ---\n" + proc.stderr[-1000:])
    (RES / "grade_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("\nwrote", RES / "grade_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["naive", "fast"]))
