#!/usr/bin/env python3
"""Discrimination report for the 2026-06-16 expansion (21 new tasks, two batches).

Reads the per-arm full eval JSONs (results/eval_<arm>_full.json from grade_all.py),
filters to the new tasks, and emits a naive-vs-fast comparison to
results/NEW_TASKS_DISCRIMINATION.md, split into:
  * batch-1 (14): fully-specified spec-density / multi-file / stats tasks;
  * batch-2 / tier-2 (7): hard complexity gates, a large reactive system, and
    subtle boundary-ambiguity tasks — built so a single shot can actually fail.

Usage:  python3 experiment_mihaco/report_newtasks.py
"""
from __future__ import annotations

import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
RES = EXP / "results"

# (category, id, weight, style, tier)
TASKS = [
    ("swe_bench", "swe05_ledger_balance", 6, "SWE multi-file: dropped debit entries", 1),
    ("swe_bench", "swe06_lru_writeback", 6, "SWE multi-file: stale read after write", 1),
    ("swe_bench", "swe07_router_dispatch", 6, "SWE multi-file: trailing-slash normalization", 1),
    ("swe_bench", "swe08_money_rounding", 6, "SWE multi-file: truncate-vs-round tax", 1),
    ("complex", "c07_migration_runner", 5, "spec-density: int-vs-string version order", 1),
    ("complex", "c08_pivot_report", 5, "spec-density: NaN-vs-0 fill + tie-break", 1),
    ("easy", "e06_semver_order", 1, "spec-density: numeric pre-release order", 1),
    ("compositional", "cb05_config_validator", 4, "multi-lib: exception precedence", 1),
    ("compositional", "cb06_timeseries_resample", 4, "multi-lib: NaN-aware zscore/mean", 1),
    ("compositional", "cb07_graph_spectral", 4, "multi-lib: Fiedler = 2nd eigenvalue", 1),
    ("data_analysis", "d07_paired_design", 3, "stats twist: paired vs unpaired t-test", 1),
    ("data_analysis", "d08_multiple_comparisons", 3, "stats twist: Holm correction", 1),
    ("long_horizon", "lh11_index_build", 3, "cascade: 6-step TF-IDF (df bug)", 1),
    ("long_horizon", "lh12_budget_forecast", 4, "cascade: 8-step forecast", 1),
    # ---- tier-2 (built to fail single-shot) ----
    ("competitive", "cp05_kth_subarray_sum", 8, "HARD GATE: kth subarray sum (O(n log V))", 2),
    ("competitive", "cp06_range_distinct_offline", 8, "HARD GATE: offline range-distinct (BIT)", 2),
    ("algorithmic", "a08_cooldown_profit", 8, "HARD GATE + greedy trap: cooldown DP", 2),
    ("algorithmic", "a09_interval_stab", 4, "ambiguity: closed-vs-half-open endpoints", 2),
    ("complex", "c09_reactive_engine", 5, "large system: transitive cache invalidation", 2),
    ("debug", "dbg07_token_bucket", 2, "ambiguity: refill-vs-admit ordering", 2),
    ("compositional", "cb08_cursor_paginate", 4, "ambiguity: exclusive cursor + tie-break", 2),
]


def load_arm(arm: str) -> dict:
    f = RES / f"eval_{arm}_full.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text())
    return {r["id"]: r for r in data.get("tasks", [])}


def cell(r):
    if not r:
        return "— (no sol)"
    tag = "PASS" if r["strict"] else f"{r['partial']:.2f}"
    return f"{r['passed']}/{r['total']} ({tag})"


def main() -> int:
    arms = ["naive", "fast"]
    rows = {a: load_arm(a) for a in arms}
    missing = [a for a in arms if not rows[a]]
    if missing:
        print("WARNING: missing eval files for:", missing,
              "(run: python3 experiment_mihaco/grade_all.py naive fast)")

    out = []
    out.append("# MiHaCoBench — New-Task Discrimination Report (2026-06-16 expansion)")
    out.append("")
    out.append("Two harness arms held at **Sonnet 4.6**, spec-only isolation, graded by the suite's own "
               "independent graders. `naive` = 1 single-shot implementer; `fast` = devil ∥ research → "
               "implementer (3 subagents). Reference: the earlier pilot scored naive **34/35 (≈0.97)** "
               "on the original tasks. Cell = `passed/total (PASS | partial)`.")
    out.append("")

    agg = {}
    for tier, title in [(1, "Batch 1 — fully-specified spec-density / multi-file / stats (14 tasks)"),
                        (2, "Batch 2 / tier-2 — hard gates + large system + boundary ambiguity (7 tasks)")]:
        out.append(f"## {title}")
        out.append("")
        out.append("| task | style | naive | fast |")
        out.append("|---|---|---|---|")
        a = {x: {"strict": 0, "wsum": 0.0, "w": 0.0, "n": 0} for x in arms}
        for cat, tid, w, style, tr in TASKS:
            if tr != tier:
                continue
            rn, rf = rows["naive"].get(tid), rows["fast"].get(tid)
            out.append(f"| `{tid}` | {style} | {cell(rn)} | {cell(rf)} |")
            for arm, r in (("naive", rn), ("fast", rf)):
                if r:
                    a[arm]["strict"] += r["strict"]
                    a[arm]["wsum"] += w * r["partial"]
                    a[arm]["w"] += w
                    a[arm]["n"] += 1
        agg[tier] = a
        out.append("")
        out.append("| arm | strict | weighted-partial | graded |")
        out.append("|---|---|---|---|")
        for arm in arms:
            g = a[arm]
            wp = g["wsum"] / g["w"] if g["w"] else 0.0
            out.append(f"| {arm} | {g['strict']}/{g['n']} | {wp:.3f} | {g['n']} |")
        out.append("")

    # Discriminators: tasks where naive and fast disagree (different strict, or a
    # partial gap) — these are the tasks where the harness actually moved the needle.
    discs = []
    for cat, tid, w, style, tr in TASKS:
        rn, rf = rows["naive"].get(tid), rows["fast"].get(tid)
        if rn and rf and (rn["strict"] != rf["strict"] or abs(rn["partial"] - rf["partial"]) >= 0.1):
            discs.append((tid, rn, rf, style))

    # Finding
    b1n, b2n = agg.get(1, {}).get("naive", {}), agg.get(2, {}).get("naive", {})
    b2f = agg.get(2, {}).get("fast", {})
    out.append("## Finding")
    out.append("")
    if discs:
        out.append("**Harness discriminators (naive ≠ fast):**")
        for tid, rn, rf, style in discs:
            out.append(f"* `{tid}` ({style}) — naive {cell(rn)} vs fast {cell(rf)}: the single-shot "
                       "arm gets it wrong; the harness's review/iteration catches it.")
        out.append("")
    else:
        out.append("**No harness discriminator surfaced this run** (naive == fast on every graded task).")
        out.append("")
    out.append(f"* **Batch 1** (fully specified): naive **{b1n.get('strict', 0)}/{b1n.get('n', 0)}** strict. "
               "Every trap is spelled out in `TASK.md`, so a careful frontier model avoids it — these "
               "validate coverage but do **not** discriminate at single-shot.")
    out.append(f"* **Tier-2** (built to fail single-shot): naive **{b2n.get('strict', 0)}/{b2n.get('n', 0)}** "
               f"strict, fast **{b2f.get('strict', 0)}/{b2f.get('n', 0)}** strict. The hard-gate tasks "
               "reject a naive/wrong-complexity solution by *feasibility* (it times out — not avoidable "
               "by reading), and the ambiguity tasks turn on a boundary the spec states precisely but is "
               "easy to misimplement. Lower strict counts and/or a naive-vs-fast gap here are the "
               "intended discrimination.")
    out.append("")
    out.append("_n=1 per arm; Sonnet 4.6; spec-only isolation. Exploratory, not statistically significant "
               "— see `COMPARISON_LOG.md` caveats._")
    out.append("")

    target = RES / "NEW_TASKS_DISCRIMINATION.md"
    target.write_text("\n".join(out))
    print("\n".join(out))
    print("\nwrote", target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
