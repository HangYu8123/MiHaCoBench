#!/usr/bin/env python3
"""Build the discrimination report for the 2026-06-16 hard expansion (14 tasks).

Reads the per-arm full eval JSONs written by grade_all.py
(results/eval_<arm>_full.json), filters to the 14 newly-added tasks, and emits a
naive-vs-fast comparison to results/NEW_TASKS_DISCRIMINATION.md.

The point: the original suite is solved ~one-shot by a strong model (the earlier
pilot scored naive 34/35). If the new tasks drop that strict-pass rate and/or the
fast harness beats naive on them, the new tasks discriminate as designed.

Usage:  python3 experiment_mihaco/report_newtasks.py
"""
from __future__ import annotations

import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
RES = EXP / "results"

NEW = [
    ("swe_bench", "swe05_ledger_balance", "SWE multi-file: dropped debit entries (sign bug across module)"),
    ("swe_bench", "swe06_lru_writeback", "SWE multi-file: stale read — LRU.put skips overwrite"),
    ("swe_bench", "swe07_router_dispatch", "SWE multi-file: trailing-slash path normalization"),
    ("swe_bench", "swe08_money_rounding", "SWE multi-file: truncate-vs-round per-line tax"),
    ("complex", "c07_migration_runner", "spec-density: int-vs-string migration version ordering"),
    ("complex", "c08_pivot_report", "spec-density: NaN-vs-0 fill + tie-break"),
    ("easy", "e06_semver_order", "spec-density: numeric pre-release precedence"),
    ("compositional", "cb05_config_validator", "multi-lib: ordered exception precedence (KeyError first)"),
    ("compositional", "cb06_timeseries_resample", "multi-lib: NaN-aware zscore/mean"),
    ("compositional", "cb07_graph_spectral", "multi-lib: Fiedler = 2nd-smallest eigenvalue"),
    ("data_analysis", "d07_paired_design", "stats twist: paired vs unpaired t-test"),
    ("data_analysis", "d08_multiple_comparisons", "stats twist: Holm-corrected pairwise"),
    ("long_horizon", "lh11_index_build", "cascade: 6-step TF-IDF (df bug)"),
    ("long_horizon", "lh12_budget_forecast", "cascade: 8-step forecast (reversed cumsum)"),
]
IDS = [i for _, i, _ in NEW]


def load_arm(arm: str) -> dict:
    f = RES / f"eval_{arm}_full.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text())
    return {r["id"]: r for r in data.get("tasks", [])}


def main() -> int:
    arms = ["naive", "fast"]
    rows = {a: load_arm(a) for a in arms}
    missing = [a for a in arms if not rows[a]]
    if missing:
        print("WARNING: missing eval files for:", missing,
              "(run: python3 experiment_mihaco/grade_all.py naive fast)")

    lines = []
    lines.append("# MiHaCoBench — New-Task Discrimination Report (2026-06-16 hard expansion)")
    lines.append("")
    lines.append("Two harness arms (held at **Sonnet 4.6**, spec-only isolation) over the **14 new "
                 "tasks**, graded by the suite's own independent graders. `naive` = 1 single-shot "
                 "implementer; `fast` = devil ∥ research → implementer (3 subagents). Compare to the "
                 "earlier pilot where naive scored **34/35 strict (≈0.97)** on the original tasks.")
    lines.append("")
    lines.append("| task | style | naive | fast |")
    lines.append("|---|---|---|---|")

    agg = {a: {"strict": 0, "wsum": 0.0, "w": 0.0, "n": 0} for a in arms}
    WEIGHT = {"swe_bench": 6, "complex": 5, "easy": 1, "compositional": 4,
              "data_analysis": 3, "long_horizon": {"lh11_index_build": 3, "lh12_budget_forecast": 4}}

    def cell(r):
        if not r:
            return "— (no sol)"
        tag = "PASS" if r["strict"] else f"{r['partial']:.2f}"
        return f"{r['passed']}/{r['total']} ({tag})"

    for cat, tid, style in NEW:
        rn = rows["naive"].get(tid)
        rf = rows["fast"].get(tid)
        lines.append(f"| `{tid}` | {style} | {cell(rn)} | {cell(rf)} |")
        w = WEIGHT[cat][tid] if isinstance(WEIGHT[cat], dict) else WEIGHT[cat]
        for a, r in (("naive", rn), ("fast", rf)):
            if r:
                agg[a]["strict"] += r["strict"]
                agg[a]["wsum"] += w * r["partial"]
                agg[a]["w"] += w
                agg[a]["n"] += 1

    lines.append("")
    lines.append("## Aggregate over the 14 new tasks")
    lines.append("")
    lines.append("| arm | strict pass | weighted-partial | tasks graded |")
    lines.append("|---|---|---|---|")
    for a in arms:
        g = agg[a]
        wp = g["wsum"] / g["w"] if g["w"] else 0.0
        lines.append(f"| {a} | {g['strict']}/{g['n']} | {wp:.3f} | {g['n']} |")
    lines.append("")
    ns = agg["naive"]["strict"]
    nn = agg["naive"]["n"] or 1
    fs = agg["fast"]["strict"]
    fn = agg["fast"]["n"] or 1
    lines.append("## Finding")
    lines.append("")
    if ns == nn and fs == fn:
        lines.append(f"**Both arms strict-passed all {nn} new tasks (naive {ns}/{nn}, fast {fs}/{fn}).** "
                     "The graders are *valid* (each fails its broken reference), but at this "
                     "difficulty/specification level the tasks are **not yet discriminating** for a "
                     "frontier model: every trap (use `ttest_rel`, integer-order versions, fill 0 not "
                     "NaN, exception precedence, NaN-aware stats, reversed-cumsum cascade) is **spelled "
                     "out in `TASK.md`**, and a careful model that reads the fully-specified contract "
                     "avoids it. This mirrors the original suite (pilot: naive 34/35) and the project's "
                     "own conclusion that *harness value concentrates on under-specified / genuinely-hard "
                     "work, not on well-specified tasks a strong model one-shots.*")
        lines.append("")
        lines.append("**To actually discriminate, a task must sit in the regime where a single shot "
                     "*fails*** — i.e. one of: (a) genuine algorithmic hardness behind a tight "
                     "complexity/feasibility gate (LiveCodeBench-Hard / BigO(Bench): a wrong or naive "
                     "solution physically times out — not avoidable by careful reading); (b) a large, "
                     "intricate multi-module system with enough interacting constraints that one-shot "
                     "correctness is unlikely (BigCodeBench-Hard); or (c) a deliberately **subtle / "
                     "under-specified** clause the grader silently enforces (the `c01` mechanism — the "
                     "one task that actually split the arms in the pilot). The valid path forward is a "
                     "harder *tier-2* batch built on (a)+(b), and optionally (c).")
    else:
        lines.append(f"**naive {ns}/{nn} strict, fast {fs}/{fn} strict** over the new tasks (vs ~0.97 on "
                     "the original suite). Where naive < fast, the harness added measurable value; where "
                     "both miss, the task is hard for this model class. n=1 per arm — exploratory.")
    lines.append("")
    lines.append("_n=1 per arm; model = Sonnet 4.6; spec-only isolation. Exploratory, not statistically "
                 "significant — see `COMPARISON_LOG.md` caveats._")
    lines.append("")

    out = RES / "NEW_TASKS_DISCRIMINATION.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print("\nwrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
