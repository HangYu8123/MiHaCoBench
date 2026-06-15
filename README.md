# HarnessFlow PyBench

A Python coding benchmark for evaluating coding **agents and harnesses** — not just
models. Inspired by *Harness Bench* (Jason Upchurch / Endor Labs), *Vibe Code Bench
v1.1*, and the methodology of HumanEval, MBPP, SWE-bench, BigCodeBench, ClassEval,
DS-1000, LiveCodeBench, BigO(Bench), SlopCodeBench, and TheAgentCompany.

> Created 2026-06-15. Tasks were authored against a pinned, offline Python 3.11.5
> environment to minimise training-data contamination and guarantee reproducibility.

## What it measures

35 tasks across six categories that stress different abilities of a coding harness:

| Category | Count | What it probes | Per-task weight |
|---|---|---|---|
| `easy` | 5 | single-file (~100 LOC), ≤4 packages — baseline competence | 1 |
| `complex` | 5 | ~1000 LOC, multi-file/multi-class, ≥2 packages incl. a **large** one (SQLAlchemy) | 5 |
| `data_analysis` | 5 | load → analyse → **correct statistics** → **visualise** | 3 |
| `algorithmic` | 5 | LeetCode-style; **time / space complexity** + readability (1 easy, 1 medium, 3 hard) | 2 / 4 / 8 |
| `long_horizon` | 10 | dependency chains of 2,4,…,20 steps — a wrong early step **cascades** | steps/2 |
| `ml` | 5 | common ML tasks via scikit-learn — held-out, leakage-resistant | 3 |

See [`RUBRIC.md`](RUBRIC.md) for the full scoring methodology.

## How a task is structured

```
tasks/<category>/<task_id>/
  TASK.md          # the ONLY thing the agent under test is shown: prompt + exact contract
  task.json        # machine-readable manifest (id, category, weight, packages, steps, entrypoints)
  grader/test_*.py # independent pytest grader — written against the contract, not any solution
  data/            # committed deterministic inputs/datasets (data_analysis, ml, long_horizon)
  expected/        # precomputed ground-truth fixtures (when applicable)

_solutions/<category>/<task_id>/          # GOLD reference (hidden from the agent under test)
_solutions/<category>/<task_id>__broken/  # deliberately-broken reference (proves the grader discriminates)
```

**Grader integrity (SWE-bench style).** Every grader must *pass* on the gold
reference and *fail* on the broken reference. `run_benchmark.py --self-check`
verifies this for all tasks — it is the benchmark's own correctness test.

**Isolation.** Gold/broken references live under `_solutions/`, a tree separate
from `tasks/`. A real evaluation gives the agent only `tasks/<…>/TASK.md` and an
empty workspace; the grader never reads the reference when a candidate is supplied.

## Running

```bash
# 0. one-time: install the pinned grader+solution dependencies
pip install -r benchmark/requirements.txt

# 1. environment preflight (all required packages importable?)
python benchmark/run_benchmark.py --preflight

# 2. validate the benchmark itself (graders pass on gold, fail on broken)
python benchmark/run_benchmark.py --self-check

# 3. evaluate a candidate harness's solutions
#    (candidate_root must contain <category>/<task_id>/ per task, OUTSIDE benchmark/tasks/)
python benchmark/run_benchmark.py --candidate-root /path/to/candidate_solutions

# scope to one category or task
python benchmark/run_benchmark.py --self-check --category algorithmic
python benchmark/run_benchmark.py --self-check --task edit_distance
```

The candidate runner writes `benchmark/results.json` with per-task and
per-category strict / partial / weighted scores.

## How code under test is resolved (env contract)

A grader never hard-codes a path. It calls `grading_utils.resolve_solution_dir`,
which honours, in order:

1. `PYBENCH_SOLUTION_DIR` — absolute path to *this* task's solution (single-task mode).
2. `PYBENCH_CANDIDATE_ROOT` — `<root>/<category>/<task_id>/`.
3. default gold under `_solutions/`; `PYBENCH_VARIANT=broken` selects the broken gold.

So the same grader runs unchanged against the gold reference or any candidate.

## Scoring at a glance

* **strict** — 1.0 only if every grader test for the task passes.
* **partial** — fraction of grader tests passed (gives partial credit; for
  `long_horizon` this tracks how far the dependency chain stayed correct).
* **weighted** — `Σ weight·partial / Σ weight`, with the weights above so a
  harness cannot inflate its score by acing only the easy tasks.

Readability and empirical Big-O scaling are **advisory** signals (reported, never
gating). Complexity is *enforced* by feasibility: a wrong-complexity solution
times out on a large adversarial input.
