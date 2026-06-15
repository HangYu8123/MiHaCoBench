# MiHaCoBench

**A Python coding benchmark for evaluating coding _agents and harnesses_ — the whole
pipeline of an AI coding system — not just raw model capability.**

![Python](https://img.shields.io/badge/python-3.11.x-blue)
![Tasks](https://img.shields.io/badge/tasks-35-success)
![Categories](https://img.shields.io/badge/categories-6-informational)
![Self-check](https://img.shields.io/badge/self--check-passing-brightgreen)

> The source code and [`RUBRIC.md`](RUBRIC.md) brand the suite internally as
> **HarnessFlow PyBench** — it is the same project as MiHaCoBench. Tasks were
> authored on **2026-06-15** against a pinned, offline **Python 3.11.5** environment
> to minimise training-data contamination and guarantee reproducibility.

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

**35 tasks across six categories**, each stressing a different ability of a coding
harness. Tasks are **weighted** when aggregating so a harness cannot inflate its
score by acing only the easy ones.

| Category | Count | What it probes | Per-task weight |
|---|---|---|---|
| `easy` | 5 | single-file (~100 LOC), stdlib/≤4 packages — baseline competence | 1 |
| `complex` | 5 | multi-file / multi-class systems (gold ≈400–800 LOC) using a large package (SQLAlchemy, jinja2, networkx, pandas) | 5 |
| `data_analysis` | 5 | load → analyse → **correct statistics** → **visualise** | 3 |
| `algorithmic` | 5 | time / space **complexity** + readability (1 easy, 1 medium, 3 hard) | 2 / 4 / 8 |
| `long_horizon` | 10 | dependency chains of 2, 4, …, 20 steps — a wrong early step **cascades** | steps / 2 |
| `ml` | 5 | scikit-learn tasks — held-out, leakage-resistant | 3 |

Example task ids: `easy/e01_csv_pulse`, `complex/c01_job_queue_sqla`,
`data_analysis/d05_experiment_anova`, `algorithmic/a04_edit_distance`,
`long_horizon/lh10_mega_etl`, `ml/m03_clustering`.

See [`RUBRIC.md`](RUBRIC.md) for the authoritative, per-category grading methodology.

## Design pillars

1. **Grader integrity (SWE-bench style).** Every grader must **pass** on a hidden
   *gold* reference and **fail** on a deliberately-*broken* reference. A task with no
   broken variant, or whose grader passes the broken one, is reported INVALID.
   `run_benchmark.py` (default mode) verifies this for all 35 tasks — it is the
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

The runner has **three modes**. Run everything from the repository root.

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

Scope any mode to one category or to tasks whose id contains a substring:

```bash
python run_benchmark.py --category algorithmic
python run_benchmark.py --task edit_distance
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
SELF-CHECK — validating 35 graders (must PASS on gold, FAIL on broken)

  [PASS] easy          e01_csv_pulse            gold 8/8   broken 5/8
  ...
SELF-CHECK: 35/35 graders valid.
```

```
EVALUATE — candidate root: /path/to/candidate_solutions
  ...
  TOTAL strict 35/35   weighted-partial 1.000
  Wrote /…/results.json
```

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
`passed/total/partial/strict`, per-category totals, `strict_total` (e.g. `35/35`),
and the overall `weighted_partial`.

Readability (`grading_utils.code_quality_report`) and the empirical Big-O fit
(`grading_utils.estimate_time_complexity`) are **advisory** — reported, never
gating. Complexity is *enforced by feasibility*: a wrong-complexity solution
physically times out on a large adversarial input.

> **Note on the committed `results.json`.** Its scores (35/35 strict,
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

## License

No `LICENSE` file is currently included in this repository. Until one is added,
treat the contents as all-rights-reserved and contact the maintainer before reuse.
