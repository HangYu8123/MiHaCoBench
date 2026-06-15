# HarnessFlow PyBench — Scoring Rubric & Grading Methodology

This document is the authority for how every task is graded. It encodes the
design decisions that came out of the Step-3 adversarial review so the benchmark
is **valid** (graders pass correct code, fail wrong code), **robust** (not flaky),
and **not gameable**.

## 1. Per-task scoring primitives

Each grader is a pytest file. The runner records, per task:

* `total`   — number of grader tests.
* `passed`  — tests that passed.
* `partial` = `passed / total`  ∈ [0, 1].
* `strict`  = 1 if `passed == total` else 0.

## 2. Weights (anti-cherry-picking)

A category's average hides whether a harness aced 5 easy tasks or 1 hard one, so
tasks are weighted when aggregating:

| Category | Weight |
|---|---|
| easy | 1 each |
| complex | 5 each |
| data_analysis | 3 each |
| algorithmic — easy / medium / hard | 2 / 4 / 8 |
| long_horizon — H steps | H / 2 (so 2-step = 1 … 20-step = 10) |
| ml | 3 each |

**Overall weighted score** = `Σ (weight · partial) / Σ weight`. The runner also
reports raw `strict` counts per category so both views are visible.

## 3. Grader-integrity invariant (mandatory for every task)

Borrowed from SWE-bench's FAIL_TO_PASS / PASS_TO_PASS idea:

* The grader **must pass** (`strict == 1`) on the gold reference.
* The grader **must fail** (`passed < total`) on the deliberately-broken reference.

`run_benchmark.py --self-check` enforces both. A task without a `__broken`
variant, or whose grader passes on the broken variant, is reported as INVALID.

Graders test the **public contract only** — never internal class/variable names,
import order, or implementation choices. Solutions are imported by file path
(`importlib`), so a candidate's internal module layout is irrelevant.

## 4. Category-specific methodology

### easy
≥6 test cases covering happy path, edge cases, and at least one adversarial input.
Pure correctness; no timing. Single file imported by path.

### complex
Method-/route-/query-level partial credit (ClassEval style): the grader exercises
each required public entrypoint independently so a partly-correct system earns
partial credit. Graded **in-process** — in-memory SQLite for SQLAlchemy, synthetic
WSGI `environ` dicts for the web framework — never a live server. Each task lists
its required public entrypoints + exact signatures in `TASK.md`. Includes
regression-style checks (P2P) where stubs exist.

### data_analysis
* Committed deterministic dataset under `data/`; the grader never generates fresh
  random data.
* Ground-truth statistics precomputed from the reference and stored in
  `expected/*.json`; the grader compares with `numpy.isclose`/relative tolerance
  (default `rtol=1e-3`). Tolerances are documented per task.
* For hypothesis tests the grader checks the **conclusion** (reject / fail-to-reject
  at α=0.05) and the **sign / order of magnitude** of the statistic — not an exact
  p-value (which drifts across library versions).
* **Surface-form constraint** (DS-1000): the solution source must invoke the
  intended statistical routine (e.g. `scipy.stats.ttest_ind`), checked via
  `grading_utils.source_uses`, so a hand-rolled approximation that happens to land
  in range does not pass.
* Plots: each required PNG is validated with Pillow for existence, non-trivial
  size, and real colour variation (`grading_utils.png_is_valid`).
* `results.json` contract: required keys must be present *and* within tolerance.

### algorithmic
Three layers, in priority order:

1. **Correctness (hard gate):** ≥8 cases incl. empty/singleton/boundary/adversarial.
2. **Complexity (hard gate, by feasibility):** one large adversarial input run under
   a tight per-task timeout (`grading_utils.time_limit`). A solution of the wrong
   time complexity cannot finish in time and fails. For the space-focused task
   (`edit_distance`) peak `tracemalloc` memory at a large input must be
   sub-quadratic. **Exact N values and timeouts are stated in each `TASK.md`.**
3. **Complexity (soft signal):** `grading_utils.estimate_time_complexity` fits the
   runtime curve over ≥5 sizes and reports the inferred class; marked
   `soft_complexity` and only fails if the fit is more than *two* tiers worse than
   target (catches egregious cases without flaky borderline failures).

Readability is **advisory only** — `grading_utils.code_quality_report` emits
docstring coverage, naming conformance, function length, and cyclomatic
complexity. These are reported, never gated (readability is human-judged).

### long_horizon
* Horizons H ∈ {2,4,6,8,10,12,14,16,18,20}. Step *k* reads **only** the artifact
  written by step *k-1* and writes `stepK.json` containing its result **and** a
  `provenance` field = SHA-256 of the exact bytes of the step *k-1* artifact.
* The grader runs steps in order; before crediting step *k* it verifies the
  `provenance` hash matches the real previous artifact. This defeats the
  "re-implement every step from scratch" gaming path and makes errors **cascade**:
  the expected value for step *k* is computed from the true chain, so a wrong step
  *k-1* yields a wrong step *k*.
* Task score uses TheAgentCompany's partial formula:
  `S = 0.5·(steps_passed / H) + 0.5·(all_steps_passed)`, with later steps implicitly
  worth more because a break stops the chain. The grader emits one test per step
  plus a final cumulative test, so the runner's generic `partial` tracks chain depth.

### ml
* The grader performs its **own** train/test split on the committed dataset; the
  solution must expose `train(X_train, y_train)` and `predict(X_test)` (or
  `fit_predict` for clustering) — never a single self-scoring entrypoint.
* Held-out performance must exceed a documented threshold.
* **Anti-leakage sanity:** the grader also fits the candidate on a *mislabelled*
  holdout and asserts accuracy collapses toward chance — a solution that memorised
  / fit the test set is caught.
* Deterministic: fixed seeds; `PYTHONHASHSEED=0` set by the runner.

## 5. Robustness rules every grader follows

* Per-category time budgets (`grading_utils.TIME_BUDGETS`), enforced as subprocess
  timeouts by the runner; a timeout = failure, no retries.
* Float comparisons use tolerances, never `==`.
* Exceptions are asserted by **type**, never by message string.
* Output-format expectations (file names, JSON keys, dtypes) are stated exactly in
  `TASK.md` — prompts are specified, not under-specified.

## 6. Contamination & isolation

* Domain-specific entrypoint names (e.g. `compute_cohort_retention`, not `solve`)
  and twists on classic problems reduce verbatim training-set recall.
* Gold/broken references live outside `tasks/`; the runner refuses a candidate
  root inside `tasks/`.
* Each `TASK.md` carries a creation date for future temporal-contamination filtering.
