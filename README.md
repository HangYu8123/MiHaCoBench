# MiHaCoBench

**A Python coding benchmark for evaluating coding _agents and harnesses_ — the whole
pipeline of an AI coding system — not just raw model capability.**

![Python](https://img.shields.io/badge/python-3.11.x-blue)
![Tasks](https://img.shields.io/badge/tasks-75-success)
![Categories](https://img.shields.io/badge/categories-11-informational)
![Self-check](https://img.shields.io/badge/self--check-passing-brightgreen)

> The source code and [`RUBRIC.md`](RUBRIC.md) brand the suite internally as
> **HarnessFlow PyBench** — it is the same project as MiHaCoBench. The original
> tasks were authored on **2026-06-15** against a pinned, offline **Python 3.11.5**
> environment to minimise training-data contamination and guarantee reproducibility;
> **21 additional hard tasks were added on 2026-06-16** — 14 spec-density/multi-file
> tasks plus a 7-task *tier-2* batch (hard complexity gates, a large reactive system,
> and subtle boundary-ambiguity tasks) built to break single-shot agents
> (see _"Distinguishing harnesses"_ below). On **2026-06-17** the suite was
> **simplified**: 17 always-tie / redundant tasks were removed and 7
> *failure-frontier* tasks were added — observation-heavy algorithms, a
> numerical-stability (catastrophic-cancellation) trap, a cumulative-state
> long-horizon ledger, a cross-module "evolution" bug, and more boundary
> ambiguity — bringing the total to **69** (see `experiment_mihaco/SIMPLIFICATION_PROPOSAL.md`).

---

## Overview

Most code benchmarks score a *model* in isolation. **MiHaCoBench scores the
harness**: prompt handling, file I/O, multi-step planning, tool use, dependency
management, and the ability to keep a long chain of work correct — everything an
agentic coding system does between reading a task and producing a working solution.

Each task hands the agent-under-test a single, fully-specified `TASK.md` and an
empty workspace. The agent writes a solution; an **independent pytest grader**
checks only the *public contract* (never internal names or layout). A solution is
imported by file path, so the harness's internal module structure is irrelevant.

The methodology draws on **HumanEval, MBPP, SWE-bench, BigCodeBench, ClassEval,
DS-1000, LiveCodeBench, BigO(Bench),** and **TheAgentCompany**.

## What it measures

The **ten core categories** below each stress a different ability of a coding
harness, **plus an experimental `harness` category of 5 tasks** (the runner now
discovers 75 task manifests in total). Tasks are **weighted** when aggregating so a
harness cannot inflate its score by acing only the easy ones.

| Category | Count | What it probes | Per-task weight |
|---|---|---|---|
| `easy` | 3 | single-file (~100 LOC), stdlib/≤4 packages — baseline competence | 1 |
| `complex` | 9 | multi-file / multi-class systems (gold ≈400–800 LOC) using a large package (SQLAlchemy, jinja2, networkx, pandas) | 5 |
| `data_analysis` | 6 | load → analyse → **correct statistics** → **visualise** | 3 |
| `algorithmic` | 9 | time / space **complexity** + readability (2 medium, 7 hard) | 4 / 8 |
| `long_horizon` | 7 | dependency chains of 2–20 steps — a wrong early step **cascades** | steps / 2 |
| `ml` | 4 | scikit-learn tasks — held-out, leakage-resistant | 3 |
| `debug` | 4 | fix a planted bug in given code (SWE-bench FAIL_TO_PASS / PASS_TO_PASS) — fault localization without regressions | 2 |
| `swe_bench` | 9 | **multi-file** mini-repo fault localization — fix a bug whose symptom crosses a module boundary, FAIL_TO_PASS + PASS_TO_PASS, grader loads ≥2 modules (SWE-bench style) | 6 |
| `compositional` | 10 | compose ≥2 (often ≥3) libraries under a precise contract with full **exception-path** coverage + surface-form checks (BigCodeBench style) | 4 |
| `competitive` | 8 | contest-level algorithms with a **hard complexity gate** + adversarial inputs; novel/twisted to resist contamination (LiveCodeBench / APPS style) | 8 |
| `harness` *(experimental)* | 5 | broad, from-scratch **implementation features** (expression evaluator, unicode normalizer, ledger engine, SQL engine, transactional KV store) built to fail a single shot — see status note below | 4–6 |

Example task ids: `easy/e01_csv_pulse`, `complex/c01_job_queue_sqla`,
`data_analysis/d05_experiment_anova`, `algorithmic/a04_edit_distance`,
`long_horizon/lh10_mega_etl`, `ml/m01_tabular_classification`, `debug/dbg02_resolve_order`,
`swe_bench/swe02_mini_orm`, `compositional/cb02_workflow_dag`,
`competitive/cp04_tree_distance`. The 2026-06-16 hard expansion added, among
others, `swe_bench/swe08_money_rounding` (per-line tax rounding bug crossing a
module boundary), `complex/c07_migration_runner` (SQLAlchemy migration ordering),
`data_analysis/d07_paired_design` (paired-vs-unpaired t-test trap), and
`long_horizon/lh12_budget_forecast` (8-step forecast cascade). The 2026-06-17
simplification added `competitive/cp07_path_xor_sum` (observation-heavy tree-XOR
with an O(n²) time gate), `compositional/cb09_streaming_covariance`
(catastrophic-cancellation trap), `long_horizon/lh13_quota_ledger`
(cumulative-budget cascade), and `swe_bench/swe09_evolve_ttl_index` (cross-module
index-consistency bug).

> **The `harness` category (experimental, 2026-06-18).** Five broad
> implementation tasks (`h04_expr_eval`, `h05_normalize_lines`,
> `h06_replay_ledger`, `h07_minisql`, `h08_txnkv`) authored to fail a single,
> no-tools shot. **Empirical finding:** at the **Opus 4.8** tier they do **not** —
> naive single-pass Opus 4.8 scored a strict 100% on all five (and on 7 further
> probes, fuzz-confirmed), so each is currently a **guaranteed naive-vs-harness
> tie**. They are retained as a difficulty ceiling / weaker-harness discriminators.
> Full method + evidence: [`experiment_mihaco/results/HARNESS_CATEGORY.md`](experiment_mihaco/results/HARNESS_CATEGORY.md)
> and [`experiment_mihaco/HARNESS_CATEGORY_RUNBOOK.md`](experiment_mihaco/HARNESS_CATEGORY_RUNBOOK.md).

See [`RUBRIC.md`](RUBRIC.md) for the authoritative, per-category grading methodology.

### Distinguishing harnesses (the 2026-06-16 hard expansion)

The original suite is **well-specified enough that a strong model often solves a
task in one shot** — so it under-discriminates between harnesses. The 14 tasks
added on 2026-06-16 are deliberately built around the failure modes that research
shows reliably separate harnesses and break single-shot agents:

* **multi-file fault localization** (`swe05`–`swe08`) — the bug's *symptom* and
  *root cause* live in different modules (SWE-bench style);
* **spec-density traps** (`c07`, `c08`, `e06`) — constraint-dense contracts with a
  single hidden ambiguity (integer-vs-string version ordering, NaN-vs-0 fill,
  numeric pre-release precedence) that a hasty pass silently drops;
* **multi-library composition + exception paths** (`cb05`–`cb07`) — compose ≥3
  libraries with full, typed exception-path coverage (BigCodeBench style);
* **statistical surface-form twists** (`d07`, `d08`) — the *memorised* answer is
  wrong (unpaired vs paired t-test; uncorrected vs Holm-corrected pairwise tests);
* **longer state cascades** (`lh11` 6-step, `lh12` 8-step) — a wrong early step
  poisons everything downstream.

Each still ships a working **gold** reference (so it is solvable) and a
deliberately-**broken** one (so the grader is provably discriminating).

#### What the validation showed (and the *tier-2* batch)

Those first 14 tasks were graded by two harness arms (a no-harness single-shot
baseline and a 3-subagent "fast" harness, both held at the same model, spec-only
isolation; see `experiment_mihaco/results/NEW_TASKS_DISCRIMINATION.md`). **Both
arms solved 14/14.** The graders are valid, but because every contract is
*fully specified*, a careful frontier model just reads the spec and avoids each
trap — so well-specified spec-density tasks alone do **not** separate harnesses.

The **tier-2 batch (7 tasks, 2026-06-16)** targets the regime where a single shot
actually *fails*:

* **hard complexity gates** — `competitive/cp05_kth_subarray_sum`,
  `competitive/cp06_range_distinct_offline`, `algorithmic/a08_cooldown_profit`: a
  naive / wrong-complexity solution **physically times out** on a large adversarial
  input (not avoidable by careful reading — BigO(Bench) shows models struggle most
  at complexity-constrained generation);
* **a large intricate system** — `complex/c09_reactive_engine`: a reactive dataflow
  engine whose **transitive cache invalidation**, topological batch recompute, and
  cycle roll-back must all be right at once;
* **subtle boundary ambiguity** (the `c01` mechanism) — `debug/dbg07_token_bucket`
  (refill-vs-admit ordering), `algorithmic/a09_interval_stab` (closed-vs-half-open
  endpoints), `compositional/cb08_cursor_paginate` (exclusive-cursor + tie-break).

## Design pillars

1. **Grader integrity (SWE-bench style).** Every grader must **pass** on a hidden
   *gold* reference and **fail** on a deliberately-*broken* reference. A task with no
   broken variant, or whose grader passes the broken one, is reported INVALID.
   `run_benchmark.py` (default mode) verifies this for all 69 tasks — it is the
   benchmark's own correctness test.
2. **Isolation.** Gold and broken references live under `_solutions/`, a tree
   entirely separate from `tasks/`. A real evaluation gives the agent only
   `tasks/<…>/TASK.md`; the runner refuses any candidate root inside `tasks/`.
3. **Reproducibility.** Committed datasets, fixed seeds, `PYTHONHASHSEED=0`,
   `MPLBACKEND=Agg`, pinned dependencies, and an offline Python 3.11.5 environment.

## Repository layout

Benchmark files live at the **repository root** (run them with `python
run_benchmark.py …`):

```
run_benchmark.py        # entry point: task runner / self-validator / scorer
conftest.py             # pytest root: sys.path bootstrap + marker registration
pytest.ini              # pytest config (discovery, addopts, markers)
requirements.txt        # pinned dependency union (offline reproducibility)
results.json            # last --candidate-root output (per-task / -category scores)
README.md, RUBRIC.md    # human docs (this file + full scoring methodology)
_lib/
  grading_utils.py      # the shared grading kernel (all primitives, once)
  AUTHORING_GUIDE.md    # task-authoring contract
tasks/<category>/<task_id>/
  TASK.md               # the ONLY file shown to the agent under test
  task.json             # manifest (id, category, weight, packages, entrypoints, …)
  grader/test_*.py      # independent pytest grader (public contract only)
  data/ expected/       # committed inputs + precomputed ground truth (where needed)
_solutions/<category>/<task_id>/          # GOLD reference (hidden from the agent)
_solutions/<category>/<task_id>__broken/  # deliberately-broken reference

.github/HarnessFlow/    # the HarnessFlow agentic-workflow pack (tooling) — NOT
                        # benchmark content; see that tree's own docs.
```

## How a single task is structured

```
tasks/<category>/<task_id>/
  TASK.md          # prompt + the exact public contract — the only thing the agent sees
  task.json        # machine-readable manifest (weight, packages, steps, entrypoints)
  grader/test_*.py # written against the contract, not against any solution
  data/            # committed deterministic inputs (data_analysis, ml, long_horizon)
  expected/        # precomputed ground-truth fixtures (when applicable)
```

The grader imports the solution **by file path** via `_lib/grading_utils.py`, so a
candidate's internal module layout never matters — only the public contract does.

## Installation

Requires **Python 3.11.x** (the suite was authored and self-validated on 3.11.5).
`requirements.txt` does not pin the interpreter, so make sure you are on 3.11
before installing.

```bash
pip install -r requirements.txt
```

This installs the union of every package any **solution** or **grader** needs:
numpy, pandas, scipy, scikit-learn, matplotlib, pillow, SQLAlchemy, jinja2,
networkx, pyyaml, joblib, and pytest.

## Usage

The runner has three **scoring/integrity** modes plus two **harness-setup**
helpers. Run everything from the repository root.

```bash
# 1. Preflight — import every required package; report what is missing.
python run_benchmark.py --preflight

# 2. Self-check (DEFAULT) — prove every grader is valid: it must PASS on the gold
#    reference and FAIL on the broken one. This is the benchmark's integrity test.
#    `--self-check` is the default, so these two are equivalent:
python run_benchmark.py
python run_benchmark.py --self-check

# 3. Evaluate a candidate — score a harness's solutions and write results.json.
#    DIR must contain <category>/<task_id>/ per task and must live OUTSIDE tasks/.
python run_benchmark.py --candidate-root /path/to/candidate_solutions
```

Two helpers prepare and inspect a run **without** needing the package environment
installed (they only read task manifests):

```bash
# 4. Scaffold an empty, isolated candidate workspace — one folder per task, each
#    holding only that task's TASK.md (+ its committed data/ inputs, when any).
#    DIR must live OUTSIDE this repo (see "Running your own harness" below).
python run_benchmark.py --scaffold-candidate /path/to/mihaco-candidate

# 5. List every task (category, id, weight, required solution module, TASK.md path)
#    — handy for driving a harness from a script.
python run_benchmark.py --list-tasks
```

Scope **any** mode to one category or to tasks whose id contains a substring:

```bash
python run_benchmark.py --category algorithmic
python run_benchmark.py --task edit_distance
python run_benchmark.py --scaffold-candidate ../cand --category complex   # filters apply here too
```

Each task is graded in an **isolated pytest subprocess** (JUnit-XML parsed back for
exact tallies) under a per-category time budget, so a crashing or looping solution
cannot take down the runner.

A candidate solution tree mirrors the task tree:

```
candidate_solutions/
  easy/e01_csv_pulse/solution.py
  complex/c01_job_queue_sqla/…        # whatever modules the contract needs
  long_horizon/lh01_two_step_tally/solution.py
  …
```

**Example output** (trimmed):

```
SELF-CHECK — validating 69 graders (must PASS on gold, FAIL on broken)

  [PASS] easy          e01_csv_pulse            gold 11/11 broken 9/11
  ...
SELF-CHECK: 69/69 graders valid.
```

```
EVALUATE — candidate root: /path/to/candidate_solutions
  ...
  TOTAL strict 69/69   weighted-partial 1.000
  Wrote /…/results.json
```

## Running your own harness against the suite

MiHaCoBench scores **whatever produced the solutions** — Claude Code, GitHub
Copilot, OpenAI Codex, your own agent, or a human — so the workflow is the same
for every harness. Only the "drive the agent" step differs per tool.

```
┌─ 1. install ──┐  ┌─ 2. scaffold ─────────┐  ┌─ 3. drive your harness ──┐  ┌─ 4. score ───┐
│ pip install   │→ │ one TASK.md per folder │→ │ agent reads TASK.md,      │→ │ --candidate- │
│ -r requirements│  │ OUTSIDE this repo      │  │ writes the solution there │  │ root <dir>   │
└───────────────┘  └────────────────────────┘  └───────────────────────────┘  └──────────────┘
```

```bash
# 1. Install deps (Python 3.11.x) and confirm the environment:
pip install -r requirements.txt && python run_benchmark.py --preflight

# 2. Lay out an isolated workspace OUTSIDE the repo (one folder per task):
python run_benchmark.py --scaffold-candidate ../mihaco-candidate

# 3. Drive your harness over ../mihaco-candidate/<category>/<task_id>/  (see below).

# 4. Score the SAME directory you scaffolded:
python run_benchmark.py --candidate-root ../mihaco-candidate
```

**Spec-only isolation — the one rule that makes results comparable.** The agent
under test may see **only** the task's `TASK.md` (and the `data/` inputs scaffolded
beside it). It must **not** see graders, the gold/broken references under
`_solutions/`, or other tasks — any of those leaks the answer. That is why
`--scaffold-candidate` **refuses any target inside this repository** and copies
*only* `TASK.md` + `data/` (never `expected/`, `grader/`, or `task.json`). Scaffold
to an external directory and point your harness at that directory, not at this repo.

**What file to write.** `--list-tasks` prints the required solution module for every
task. Most tasks expect `solution.py`; the `complex` tasks expect a named facade
module (`c01 → queue_api.py`, `c02 → app_factory.py`, `c03 → graph_engine.py`,
`c04 → sheet.py`, `c05 → pipeline.py`); `long_horizon` tasks expect a `solution.py`
exposing the `--step K --in <prev> --out <out>` CLI from their `TASK.md`. The grader
imports the solution **by file path** and reads `data/`/`expected/` from this repo, so
leftover `TASK.md`/`data/` files in the candidate folder never affect scoring.

> This repo ships root `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md`.
> Those configure the **maintainer's** HarnessFlow dev workflow — they are *not* how
> you run the benchmark. Scaffolding to an external directory keeps them out of your
> harness's way automatically.

### Claude Code (Anthropic)

**CLI, scripted over all tasks** — run headless, scoped to one folder at a time so
each invocation sees only its own `TASK.md`:

```bash
ROOT=../mihaco-candidate
find "$ROOT" -name TASK.md -print0 | while IFS= read -r -d '' t; do
  ( cd "$(dirname "$t")" \
    && claude -p "Read TASK.md and implement the solution it specifies. \
Write the solution file(s) into this directory. Do not read files outside it." \
       --permission-mode acceptEdits )
done
python run_benchmark.py --candidate-root "$ROOT"
```

`-p` runs non-interactively; `--permission-mode acceptEdits` auto-approves writes in
the working directory. Add `--bare` for a config-isolated run (skips your global
`CLAUDE.md`/MCP/hooks). **IDE / interactive:** open a task folder (or the whole
scaffold) as the workspace in the VS Code / JetBrains extension, or run `claude` from
inside a task folder, and prompt "implement TASK.md here."

### GitHub Copilot

**VS Code Agent mode** (the most reliable Copilot path): `File ▸ Open Folder` on a
task folder (or the whole scaffold), open Copilot Chat, switch the dropdown to
**Agent**, and prompt: *"Read TASK.md in this folder and implement the solution;
write the file(s) here."* A `.github/copilot-instructions.md` placed in the workspace
root is auto-injected into every request, so you can hard-code "always start by
reading TASK.md." **Copilot CLI** (the newer agentic `copilot` CLI) can do the same
from a task folder (`copilot -p "implement TASK.md"`), but unattended looping and the
exact auto-approve flag are still stabilizing — verify with `copilot --help` before
scripting it.

### OpenAI Codex

**CLI, scripted over all tasks** via `codex exec` (non-interactive):

```bash
ROOT=../mihaco-candidate
find "$ROOT" -name TASK.md -print0 | while IFS= read -r -d '' t; do
  ( cd "$(dirname "$t")" \
    && codex exec --sandbox workspace-write --ask-for-approval never \
       "Read TASK.md and implement the solution it specifies. Write the file(s) here." )
done
python run_benchmark.py --candidate-root "$ROOT"
```

`--sandbox workspace-write` confines writes to the task folder + `/tmp`; `--ask-for-
approval never` runs unattended. Codex auto-discovers `AGENTS.md` up the tree, so a
one-line `AGENTS.md` ("always read TASK.md first") in the scaffold root works across
runs. (The legacy `--full-auto` flag is deprecated — prefer the two flags above; the
Codex desktop app is the current GUI surface.)

### Any other harness (and fully manual)

The portable contract is just: **`cd` into a task folder, read `TASK.md`, write the
solution file(s) there, read nothing outside the folder.** Drop a one-line
`AGENTS.md` (or `CLAUDE.md`) saying "read TASK.md and implement it" into the scaffold
root and most agentic CLIs will auto-discover it. For a manual baseline, open each
`TASK.md`, write the solution by hand into the same folder, then run `--candidate-root`.

## How code under test is resolved (the env-var contract)

A grader never hard-codes a path. It calls `grading_utils.resolve_solution_dir`,
which honours, in order:

1. `PYBENCH_SOLUTION_DIR` — absolute path to *this* task's solution (single-task mode).
2. `PYBENCH_CANDIDATE_ROOT` — resolved as `<root>/<category>/<task_id>/`.
3. The default gold under `_solutions/`; `PYBENCH_VARIANT=broken` selects the broken gold.

So the **same grader** runs unchanged against the gold reference, the broken
reference, or any candidate — the runner just sets the right environment variable.

## Scoring

For each task the runner records:

* **partial** — `passed / runnable` (where `runnable = total − skipped`); gives
  partial credit. For `long_horizon` this tracks how far the dependency chain stayed
  correct.
* **strict** — `1` only if `runnable > 0` and **every** runnable grader test passes.
* **weighted** — `Σ (weight · partial) / Σ weight`, using the category weights above
  so easy tasks cannot dominate the total.

`--candidate-root` writes [`results.json`](results.json) with each task's
`passed/total/partial/strict`, per-category totals, `strict_total` (e.g. `69/69`),
and the overall `weighted_partial`.

Readability (`grading_utils.code_quality_report`) and the empirical Big-O fit
(`grading_utils.estimate_time_complexity`) are **advisory** — reported, never
gating. Complexity is *enforced by feasibility*: a wrong-complexity solution
physically times out on a large adversarial input.

> **Note on the committed `results.json`.** Its scores (69/69 strict,
> `weighted_partial = 1.0`) come from pointing `--candidate-root` at the **gold
> `_solutions/` tree itself** — a sanity baseline confirming the graders accept the
> reference solutions. It is **not** an independent agent result, and its
> `candidate_root` path is from the authoring machine. Generate your own
> `results.json` by evaluating your candidate tree.

## Reproducibility & contamination control

* **Determinism** — committed datasets under `data/`, precomputed ground truth under
  `expected/`, fixed seeds throughout, `PYTHONHASHSEED=0` and `MPLBACKEND=Agg` set by
  the runner. Float comparisons use tolerances; hypothesis tests check the
  *conclusion* at α=0.05, not an exact p-value (which drifts across library versions).
* **Pinned environment** — `requirements.txt` reflects the verified offline Python
  3.11.5 environment; `--preflight` fails loudly if anything is missing.
* **Contamination resistance** — domain-specific entrypoint names (e.g.
  `compute_cohort_retention`, not `solve`), twists on classic problems, hidden
  gold/broken references, and a creation date on every `TASK.md` for future
  temporal-contamination filtering.

## Further reading

* [`RUBRIC.md`](RUBRIC.md) — the authority on per-task scoring and grading mechanics.
* [`_lib/AUTHORING_GUIDE.md`](_lib/AUTHORING_GUIDE.md) — the contract for authoring a
  new task (manifest, grader, gold/broken references).
* [`_lib/grading_utils.py`](_lib/grading_utils.py) — the shared grading kernel
  (solution resolution, import-by-path, complexity/memory gates, plot validation,
  long-horizon provenance, surface-form checks).
* `.github/HarnessFlow/` — the **HarnessFlow** agentic-workflow pack used to develop
  and maintain this repo (workflows, agents, skills). It is tooling, not part of the
  benchmark under test.

## Agentic benchmark (ponytail-aligned)

Alongside the correctness suite above, the repo ships a second, **additive** harness under
[`benchmarks/agentic/`](benchmarks/agentic/) that ports the agentic *minimalism / over-engineering*
benchmark from [ponytail](https://github.com/DietrichGebert/ponytail) (MIT). Where the correctness
suite grades a candidate's `solution.py` pass/fail, this one runs a real headless `claude` Code session
per (task × arm × model) on a seeded starter file and measures **whether a harness keeps code minimal
without dropping safety or completeness**.

* **Tasks (27 self-contained):** a *safety* tier (7 surgical "implement this function" tasks with an
  implicit safety requirement, executed against adversarial input — path traversal, per-key rate-limit
  DoS, SQL injection, HMAC verification, malformed-CSV robustness, caching, newline-injection email),
  `todo-null` (a Node REST API that must survive a `null` POST), a *quality* tier (4 reuse/trace-before-fix
  tasks), and *open* (3) + *vibe* (12) LOC-only tasks. The upstream real-repo fastapi fixture tier is
  omitted (see the subsystem README to restore it).
* **Metrics (ponytail-identical):** `correct` + `safe` deterministic gates · source LOC / source file
  count (tests excluded, tracked separately) · cost / tokens / duration / turns from the CLI JSON · an
  auditable **over-engineering** LLM judge (0–3) and a **completeness** LLM judge (0–3).
* **Integrity, offline:** every instrument ships a `good`/`bad` reference proven before any API spend —
  `python benchmarks/agentic/run.py --selftest` (good passes / bad caught for all 27) and
  `python benchmarks/agentic/complete.py --selftest-offline` (gate logic, no key) both run with no API.

See [`benchmarks/agentic/README.md`](benchmarks/agentic/README.md) for the full task tables, metric
definitions, arm matrix, and run commands. This harness is independent of `run_benchmark.py` and does
not affect the correctness suite's discovery or scoring.

## License

Released under the [MIT License](LICENSE) — © 2026 Hang Yu. You may use, modify,
and redistribute the suite (including the tasks, graders, and reference solutions)
with attribution; see [`LICENSE`](LICENSE) for the full text.
