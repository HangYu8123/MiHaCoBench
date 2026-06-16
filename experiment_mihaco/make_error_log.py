#!/usr/bin/env python3
"""Build results/ERROR_LOG.md — a catalogue of CANDIDATE-side problems to seed
later code-fix tasks. Nothing is fixed here.

For every arm × task that is not a clean strict pass (strict==0, partial<1, or
total==0), re-run that one grader directly under pytest with the candidate root,
capturing -v --tb=short output (stdout+stderr — closing the gap where the runner
discarded stderr) so the exact failing test names and tracebacks are recorded.
Apparatus problems (MISSING_DIR / NO_PY_FILES / COMPILE_ERROR) from
grade_summary.json are listed too.

Usage:  python3 experiment_mihaco/make_error_log.py [naive fast general]
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
EXP = BENCH / "experiment_mihaco"
RES = EXP / "results"


def tasks_index() -> dict[str, dict]:
    idx = {}
    for m in sorted(glob.glob(str(BENCH / "tasks/*/*/task.json"))):
        d = json.loads(Path(m).read_text())
        d["_grader"] = BENCH / "tasks" / d["category"] / d["id"] / d["grader"]
        idx[d["id"]] = d
    return idx


def rerun_grader(meta: dict, arm_root: Path) -> str:
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONHASHSEED="0",
               PYBENCH_CANDIDATE_ROOT=str(arm_root))
    cmd = [sys.executable, "-m", "pytest", str(meta["_grader"]),
           "-p", "no:cacheprovider", "-v", "--tb=short", "--no-header"]
    try:
        proc = subprocess.run(cmd, cwd=str(BENCH), env=env, capture_output=True,
                              text=True, timeout=400)
        return (proc.stdout or "") + ("\n[stderr]\n" + proc.stderr if proc.stderr.strip() else "")
    except subprocess.TimeoutExpired:
        return "TIMEOUT (grader exceeded 400s — likely a wrong-complexity solution hitting the gate)"


def failing_lines(pytest_out: str) -> list[str]:
    out = []
    for ln in pytest_out.splitlines():
        if re.search(r"(FAILED|ERROR)\b", ln) and "::" in ln:
            out.append(ln.strip())
    # de-dup, keep order
    seen, uniq = set(), []
    for ln in out:
        if ln not in seen:
            seen.add(ln); uniq.append(ln)
    return uniq


def main(arms: list[str]) -> int:
    idx = tasks_index()
    summary = json.loads((RES / "grade_summary.json").read_text()) if (RES / "grade_summary.json").exists() else {}
    lines = ["# MiHaCoBench — Candidate Error Log (full 35-task run)",
             "",
             "Problems in **generated candidate code**, captured for later code-fix tasks. "
             "**Nothing here is fixed.** Apparatus bugs (workflow/grader/scripts) are excluded — those were fixed during the run.",
             ""]
    total_problem_tasks = 0
    for arm in arms:
        ev = RES / f"eval_{arm}_full.json"
        if not ev.exists():
            continue
        data = json.loads(ev.read_text())
        rows = {r["id"]: r for r in data.get("tasks", [])}
        arm_root = EXP / f"cand_{arm}"
        apparatus = {(i["cat"], i["id"]): i for i in summary.get(arm, {}).get("apparatus_issues", [])}

        bad = [r for r in data.get("tasks", []) if not (r["strict"] == 1 and r["total"] > 0)]
        lines.append(f"## Arm: `{arm}` — {len(bad)} task(s) with problems "
                     f"(strict {data.get('strict_total')}, weighted {data.get('weighted_partial')})")
        lines.append("")
        if not bad:
            lines.append("_No candidate problems — every task is a clean strict pass._\n")
            continue
        for r in sorted(bad, key=lambda x: x["id"]):
            tid = r["id"]; meta = idx.get(tid, {})
            total_problem_tasks += 1
            lines.append(f"### `{arm}` · `{meta.get('category','?')}/{tid}` — "
                         f"{r['passed']}/{r['total']} passed (partial {r['partial']}, weight {meta.get('weight','?')})")
            ap = apparatus.get((meta.get("category"), tid))
            if ap:
                lines.append(f"- **Apparatus/precheck:** {ap['kind']} — {ap['detail']}")
            kind = "NO TESTS RAN (import/collection error or missing files)" if r["total"] == 0 else "test failures"
            lines.append(f"- **Symptom:** {kind}")
            out = rerun_grader(meta, arm_root)
            fails = failing_lines(out)
            if fails:
                lines.append("- **Failing tests:**")
                for f in fails:
                    lines.append(f"  - `{f}`")
            # short traceback tail
            tail = out[-1200:].strip()
            lines.append("- **Detail (tail):**")
            lines.append("  ```")
            lines.extend("  " + l for l in tail.splitlines()[-22:])
            lines.append("  ```")
            lines.append("")
    header = [f"_Arms: {', '.join(arms)} · {total_problem_tasks} problem task(s) total._", ""]
    (RES / "ERROR_LOG.md").write_text("\n".join(lines[:4] + header + lines[4:]))
    print(f"wrote {RES/'ERROR_LOG.md'} — {total_problem_tasks} problem task(s) across arms {arms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["naive", "fast"]))
