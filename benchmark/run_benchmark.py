#!/usr/bin/env python3
"""HarnessFlow PyBench — task runner, self-validator, and scorer.

Three modes:

* ``--preflight``     Import every required package; report what is missing.
* ``--self-check``    (default) Prove every grader is *valid*: it must PASS on the
                      gold reference and FAIL on the deliberately-broken reference.
                      This is the benchmark's own integrity test.
* ``--candidate-root DIR``
                      Evaluate a candidate. ``DIR`` must contain
                      ``<category>/<task_id>/`` per task. Reports, per task and per
                      category: strict pass (all grader tests pass), partial score
                      (fraction of grader tests passed), and the RUBRIC.md weighted
                      total. ``DIR`` may not live inside ``benchmark/tasks/``.

Each task is graded in an isolated subprocess running pytest with a JUnit-XML
report, so a crashing solution cannot take down the runner and per-test tallies
are exact. Per-category time budgets (see ``_lib.grading_utils.TIME_BUDGETS``)
bound each task.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parent
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from _lib import grading_utils as gu  # noqa: E402

TASKS_ROOT = BENCH_ROOT / "tasks"
CATEGORIES = ["easy", "complex", "data_analysis", "algorithmic", "long_horizon", "ml"]


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
def discover_tasks() -> list[dict]:
    """Load every ``task.json`` manifest under ``tasks/<category>/<id>/``."""
    tasks = []
    for manifest in sorted(TASKS_ROOT.glob("*/*/task.json")):
        meta = json.loads(manifest.read_text())
        meta["_dir"] = manifest.parent
        meta["_grader"] = manifest.parent / meta["grader"]
        tasks.append(meta)
    return tasks


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #
def preflight() -> bool:
    required = {
        "numpy": "numpy", "pandas": "pandas", "scipy": "scipy",
        "scikit-learn": "sklearn", "matplotlib": "matplotlib", "pillow": "PIL",
        "SQLAlchemy": "sqlalchemy", "jinja2": "jinja2", "networkx": "networkx",
        "pyyaml": "yaml", "joblib": "joblib", "pytest": "pytest",
    }
    missing = []
    for dist, mod in sorted(required.items()):
        try:
            __import__(mod)
        except Exception:
            missing.append(dist)
    if missing:
        print("PREFLIGHT FAILED — missing packages: " + ", ".join(missing))
        print("Install with: pip install -r benchmark/requirements.txt")
        return False
    print(f"PREFLIGHT OK — all {len(required)} required packages importable.")
    return True


# --------------------------------------------------------------------------- #
# Grading one task
# --------------------------------------------------------------------------- #
def _run_pytest(grader: Path, env_extra: dict, timeout: float) -> dict:
    """Run a grader file under pytest with a JUnit report. Returns
    ``{passed, failed, errors, total, timed_out, returncode}``."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        xml = Path(td) / "report.xml"
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONHASHSEED="0", **env_extra)
        cmd = [sys.executable, "-m", "pytest", str(grader),
               "-p", "no:cacheprovider", "--junitxml", str(xml), "-q", "--tb=line"]
        try:
            proc = subprocess.run(cmd, cwd=str(BENCH_ROOT), env=env,
                                  capture_output=True, text=True, timeout=timeout)
            rc = proc.returncode
            timed_out = False
            tail = (proc.stdout or "")[-1500:]
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "errors": 1, "skipped": 0, "total": 0,
                    "timed_out": True, "returncode": -1, "tail": "TIMEOUT"}
        passed = failed = errors = skipped = total = 0
        if xml.exists():
            root = ET.parse(xml).getroot()
            suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
            for s in suites:
                total += int(s.get("tests", 0))
                failed += int(s.get("failures", 0))
                errors += int(s.get("errors", 0))
                skipped += int(s.get("skipped", 0))
            passed = total - failed - errors - skipped
        return {"passed": passed, "failed": failed, "errors": errors,
                "skipped": skipped, "total": total, "timed_out": timed_out,
                "returncode": rc, "tail": tail}


def grade_task(meta: dict, env_extra: dict) -> dict:
    budget = gu.TIME_BUDGETS.get(meta["category"], 120)
    steps = meta.get("steps") or 1
    timeout = budget * (steps if meta["category"] == "long_horizon" else 1) + 60
    res = _run_pytest(meta["_grader"], env_extra, timeout=timeout)
    # Score over RUNNABLE tests only: a skipped test neither passes nor fails, so
    # it must not deflate partial credit or block a strict pass.
    runnable = max(res["total"] - res.get("skipped", 0), 0)
    res["runnable"] = runnable
    res["partial"] = round(res["passed"] / runnable, 4) if runnable else 0.0
    res["strict"] = int(runnable > 0 and res["passed"] == runnable)
    return res


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #
def self_check(tasks: list[dict]) -> int:
    print(f"\nSELF-CHECK — validating {len(tasks)} graders (must PASS on gold, FAIL on broken)\n")
    bad = 0
    for m in tasks:
        gold = grade_task(m, {"PYBENCH_VARIANT": ""})
        broken_dir = gu.GOLD_ROOT / m["category"] / f"{m['id']}__broken"
        has_broken = broken_dir.is_dir()
        broken = grade_task(m, {"PYBENCH_VARIANT": "broken"}) if has_broken else None

        gold_ok = gold["strict"] == 1 and gold["total"] > 0
        # A discriminating grader does NOT fully pass on the broken variant
        # (at least one runnable test fails).
        broken_ok = (broken is not None) and broken["runnable"] > 0 and broken["strict"] == 0
        ok = gold_ok and (broken_ok if has_broken else False)
        bad += 0 if ok else 1
        flag = "PASS" if ok else "FAIL"
        bnote = (f"broken {broken['passed']}/{broken['total']}" if broken else "NO BROKEN VARIANT")
        print(f"  [{flag}] {m['category']:13} {m['id']:24} "
              f"gold {gold['passed']}/{gold['total']}  {bnote}")
        if not ok and gold.get("tail"):
            print("        gold tail:", gold["tail"].replace("\n", " ")[:200])
    print(f"\nSELF-CHECK: {len(tasks) - bad}/{len(tasks)} graders valid.")
    return 1 if bad else 0


def evaluate(tasks: list[dict], candidate_root: Path) -> int:
    candidate_root = candidate_root.resolve()
    if (TASKS_ROOT.resolve() in candidate_root.parents) or candidate_root == TASKS_ROOT.resolve():
        print("ERROR: candidate root may not be inside benchmark/tasks/ (isolation).")
        return 2
    print(f"\nEVALUATE — candidate root: {candidate_root}\n")
    rows = []
    cat_tot: dict[str, dict] = {c: {"weight": 0.0, "weighted": 0.0, "strict": 0, "n": 0} for c in CATEGORIES}
    for m in tasks:
        res = grade_task(m, {"PYBENCH_CANDIDATE_ROOT": str(candidate_root)})
        w = float(m.get("weight", 1))
        rows.append({"id": m["id"], "category": m["category"], "weight": w,
                     "passed": res["passed"], "total": res["total"],
                     "partial": res["partial"], "strict": res["strict"]})
        c = cat_tot[m["category"]]
        c["weight"] += w
        c["weighted"] += w * res["partial"]
        c["strict"] += res["strict"]
        c["n"] += 1
        print(f"  {m['category']:13} {m['id']:24} {res['passed']:>3}/{res['total']:<3} "
              f"partial={res['partial']:.2f} strict={res['strict']} (w={w:g})")

    print("\n  Category                strict     partial(weighted)")
    tot_w = tot_ww = 0.0
    tot_strict = tot_n = 0
    for c in CATEGORIES:
        d = cat_tot[c]
        if d["n"] == 0:
            continue
        frac = d["weighted"] / d["weight"] if d["weight"] else 0.0
        print(f"  {c:20} {d['strict']:>2}/{d['n']:<2}      {frac:.3f}")
        tot_w += d["weight"]; tot_ww += d["weighted"]
        tot_strict += d["strict"]; tot_n += d["n"]
    print(f"\n  TOTAL strict {tot_strict}/{tot_n}   weighted-partial {tot_ww/tot_w if tot_w else 0:.3f}")

    out = {"candidate_root": str(candidate_root), "tasks": rows,
           "category_totals": cat_tot,
           "strict_total": f"{tot_strict}/{tot_n}",
           "weighted_partial": round(tot_ww / tot_w, 4) if tot_w else 0.0}
    report = BENCH_ROOT / "results.json"
    report.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n  Wrote {report}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="HarnessFlow PyBench runner")
    ap.add_argument("--preflight", action="store_true", help="check required packages only")
    ap.add_argument("--self-check", action="store_true", help="validate graders against gold+broken")
    ap.add_argument("--candidate-root", type=Path, help="evaluate a candidate solution tree")
    ap.add_argument("--category", choices=CATEGORIES, help="limit to one category")
    ap.add_argument("--task", help="limit to one task id (substring match)")
    args = ap.parse_args(argv)

    if args.preflight:
        return 0 if preflight() else 1
    if not preflight():
        return 1

    tasks = discover_tasks()
    if args.category:
        tasks = [t for t in tasks if t["category"] == args.category]
    if args.task:
        tasks = [t for t in tasks if args.task in t["id"]]
    if not tasks:
        print("No tasks discovered (did the task authors run yet?).")
        return 1

    if args.candidate_root:
        return evaluate(tasks, args.candidate_root)
    return self_check(tasks)


if __name__ == "__main__":
    raise SystemExit(main())
