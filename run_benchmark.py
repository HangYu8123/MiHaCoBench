#!/usr/bin/env python3
"""HarnessFlow PyBench — task runner, self-validator, and scorer.

Scoring / integrity modes (these need the package environment installed):

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

Harness-setup helpers (no package environment required — these only read task
manifests, so you can prepare a run before ``pip install``):

* ``--scaffold-candidate DIR``
                      Lay out an empty, isolated candidate workspace: one
                      ``<category>/<task_id>/`` folder per task, each holding ONLY
                      that task's ``TASK.md`` (plus its committed ``data/`` inputs,
                      when any). Point any coding harness at ``DIR``, let it write
                      each task's solution there, then score the *same* ``DIR`` with
                      ``--candidate-root``. ``DIR`` must live OUTSIDE this repo so the
                      agent under test cannot see graders, gold references, or other
                      tasks.
* ``--list-tasks``    Print every task's category, id, weight, required solution
                      module, and ``TASK.md`` path — for driving a harness from a
                      script.

Each task is graded in an isolated subprocess running pytest with a JUnit-XML
report, so a crashing solution cannot take down the runner and per-test tallies
are exact. Per-category time budgets (see ``_lib.grading_utils.TIME_BUDGETS``)
bound each task.

All modes accept ``--category`` / ``--task`` to scope to a subset.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parent
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from _lib import grading_utils as gu  # noqa: E402

TASKS_ROOT = BENCH_ROOT / "tasks"
# New categories are APPENDED (never inserted) so results.json category order stays stable.
CATEGORIES = ["easy", "complex", "data_analysis", "algorithmic", "long_horizon", "ml", "debug",
              "swe_bench", "compositional", "competitive", "harness"]


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
        print("Install with: pip install -r requirements.txt")
        return False
    print(f"PREFLIGHT OK — all {len(required)} required packages importable.")

    # Report whether the hard complexity gate (the Big-O feasibility check the
    # algorithmic/competitive graders rely on) can actually enforce here, so an
    # unsound platform is loud rather than silently passing wrong-complexity code.
    mech = gu.complexity_gate_mechanism()
    if mech == "sigalrm":
        print("COMPLEXITY GATE: SIGALRM enforcement active (hard wall-clock gate).")
    elif mech == "thread-watchdog":
        print("COMPLEXITY GATE: WARNING — SIGALRM unavailable (non-POSIX or non-main-"
              "thread); using the thread-watchdog fallback. It interrupts pure-Python "
              "runaway loops but cannot pre-empt a long call inside a C extension. Run "
              "the suite on a POSIX main thread for the strongest algorithmic/competitive "
              "complexity gating.")
    else:
        print("COMPLEXITY GATE: WARNING — no wall-clock enforcement available here; "
              "wrong-complexity solutions will NOT be timed out, so algorithmic/"
              "competitive results are unsound on this platform.")
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


# --------------------------------------------------------------------------- #
# Harness-setup helpers (no package environment required)
# --------------------------------------------------------------------------- #
def _entry_module(meta: dict) -> str:
    """The primary solution filename the grader imports for this task.

    Most tasks expect ``solution.py``; the ``complex`` tasks expect a named
    facade module (e.g. ``queue_api.py``). Always read it from the manifest so
    scaffolding never tells the agent the wrong filename.
    """
    return (meta.get("entrypoints") or {}).get("module") or "solution.py"


def scaffold_candidate(tasks: list[dict], dst: Path) -> int:
    """Lay out an empty, isolated candidate workspace under ``dst``.

    For each task, create ``dst/<category>/<task_id>/`` containing only that
    task's ``TASK.md`` (the sole spec the agent under test may see) plus its
    committed ``data/`` inputs when present. ``expected/`` ground truth,
    graders, and ``task.json`` are never copied. ``dst`` must live outside this
    repository so the agent cannot read graders, gold references, or sibling
    tasks.
    """
    dst = dst.resolve()
    bench = BENCH_ROOT.resolve()
    if dst == bench or bench in dst.parents:
        print("ERROR: --scaffold-candidate DIR must live OUTSIDE this repository "
              "(isolation: the agent under test must not see graders/gold/other tasks).")
        print(f"       Pick a path outside {bench}, e.g.  {bench.parent / 'mihaco-candidate'}")
        return 2
    print(f"\nSCAFFOLD — preparing {len(tasks)} task workspace(s) under {dst}\n")
    with_data = 0
    for m in tasks:
        out = dst / m["category"] / m["id"]
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(m["_dir"] / "TASK.md", out / "TASK.md")
        data_src = m["_dir"] / "data"
        note = ""
        if data_src.is_dir():
            shutil.copytree(data_src, out / "data", dirs_exist_ok=True)
            with_data += 1
            note = "  (+ data/)"
        print(f"  {m['category']:13} {m['id']:26} → write {_entry_module(m):16}{note}")
    print(f"\n  {len(tasks)} folder(s) ready ({with_data} with committed data/).")
    print("  Each folder holds only TASK.md — drive your harness there, one task per folder,")
    print("  writing the solution module named above next to each TASK.md. Then score it:")
    print(f"\n      python run_benchmark.py --candidate-root {dst}\n")
    return 0


def list_tasks(tasks: list[dict]) -> int:
    """Print one row per task (category, id, weight, required module, steps,
    TASK.md path) so a harness can be driven from a script."""
    print(f"\n{'category':13} {'task_id':26} {'w':>3} {'module':16} {'steps':>5}  TASK.md")
    for m in tasks:
        steps = m.get("steps") or "-"
        task_md = (m["_dir"] / "TASK.md").relative_to(BENCH_ROOT)
        print(f"{m['category']:13} {m['id']:26} {float(m.get('weight', 1)):>3g} "
              f"{_entry_module(m):16} {str(steps):>5}  {task_md}")
    print(f"\n  {len(tasks)} task(s).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="HarnessFlow PyBench runner")
    ap.add_argument("--preflight", action="store_true", help="check required packages only")
    ap.add_argument("--self-check", action="store_true", help="validate graders against gold+broken")
    ap.add_argument("--candidate-root", type=Path, help="evaluate a candidate solution tree")
    ap.add_argument("--scaffold-candidate", type=Path, metavar="DIR",
                    help="prepare an empty, isolated candidate workspace at DIR (one TASK.md per task)")
    ap.add_argument("--list-tasks", action="store_true",
                    help="list every task (category, id, weight, required module, TASK.md path)")
    ap.add_argument("--category", choices=CATEGORIES, help="limit to one category")
    ap.add_argument("--task", help="limit to one task id (substring match)")
    args = ap.parse_args(argv)

    if args.preflight:
        return 0 if preflight() else 1

    # Discovery only reads JSON manifests, so the harness-setup helpers run
    # without the package environment; only scoring/self-check needs preflight.
    tasks = discover_tasks()
    if args.category:
        tasks = [t for t in tasks if t["category"] == args.category]
    if args.task:
        tasks = [t for t in tasks if args.task in t["id"]]
    if not tasks:
        print("No tasks discovered (did the task authors run yet?).")
        return 1

    if args.scaffold_candidate:
        return scaffold_candidate(tasks, args.scaffold_candidate)
    if args.list_tasks:
        return list_tasks(tasks)

    if not preflight():
        return 1
    if args.candidate_root:
        return evaluate(tasks, args.candidate_root)
    return self_check(tasks)


if __name__ == "__main__":
    raise SystemExit(main())
