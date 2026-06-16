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
| debug | 2 each |
| swe_bench | 6 each |
| compositional | 4 each |
| competitive | 8 each |

Adding the `swe_bench`, `compositional`, and `competitive` categories grows the
weighted-score denominator, so a `weighted_partial` over the expanded suite is
**not** directly comparable to one from the earlier 40-task suite. Compare scores
only within the same suite revision (see the regenerated `results.json`).

`swe_bench` is weighted **6** — above single-file `complex` (5) because a fix must
be *localised across multiple modules* without regressing the PASS_TO_PASS guard.
`competitive` is weighted **8** (the algorithmic-hard tier) because each task
demands an asymptotically-correct algorithm under a hard feasibility gate.
`compositional` is weighted **4** — above `data_analysis` (3) for its mandatory
multi-library composition and exhaustive exception-path coverage, below `complex`
since each is a single function/module.

**Overall weighted score** = `Σ (weight · partial) / Σ weight`. The runner also
reports raw `strict` counts per category so both views are visible.

`debug` is weighted **2** — above `easy` (1) because a debug task requires
*localising* a planted fault and fixing it **without regressing** the behaviour
the buggy code already gets right (the PASS_TO_PASS guard), but below the
multi-file `complex` tier since each task is a single `solution.py`. Note that
adding the `debug` category increases the weighted-score denominator, so a
`weighted_partial` computed over 40 tasks is not directly comparable to one from
the earlier 35-task suite.

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
* Horizons H ∈ {2,4,6,8,10,12,14,16,18,20}, plus two additional cascades at H=6
  (`lh11_index_build`, a TF-IDF search index) and H=8 (`lh12_budget_forecast`)
  added in the 2026-06-16 hard expansion. Step *k* reads **only** the artifact
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

### debug
Modelled on **SWE-bench's FAIL_TO_PASS / PASS_TO_PASS** split. The `TASK.md`
embeds a *buggy* implementation plus a concrete repro (input → wrong output →
expected output); the agent returns a corrected single-file `solution.py`.

* **FAIL_TO_PASS** tests exercise the exact behaviour the planted bug breaks —
  they fail on the buggy code and pass only on a correct fix.
* **PASS_TO_PASS** tests guard the behaviour the buggy code already gets right, so
  a fix that regresses unrelated behaviour is rejected.
* The deliberately-**broken** reference *is* the still-buggy code (rather than a
  different defect), so `--self-check` directly proves the FAIL_TO_PASS tests
  discriminate. The planted bug is **localized** — the broken reference still
  passes every PASS_TO_PASS test — and at least one FAIL_TO_PASS test must fail on
  it.
* Bug descriptions are stated **behaviourally**, not structurally (no "fix this
  line" hints), and tests pin behaviour precisely enough that a *partial* fix
  (e.g. one that addresses only one code path) does not earn full credit.
* Single file, stdlib-only, ≥6 tests + advisory `code_quality` — same mechanics
  as `easy`.

### swe_bench
The **multi-file** escalation of `debug`, modelled on **SWE-bench** (repo-level
FAIL_TO_PASS / PASS_TO_PASS). Each task ships a small Python **package** (3–5
importable modules) under `_solutions/swe_bench/<id>/` with a planted fault whose
*symptom crosses a module boundary*; `TASK.md` describes the observed behaviour
**behaviourally** (never "fix file X line Y"). The agent returns the corrected
package.

* **FAIL_TO_PASS** tests exercise the cross-module behaviour the bug breaks; at
  least one must fail on the broken reference. Several F2P tests use inputs **not**
  shown in `TASK.md` so a fix cannot be hard-coded to the stated reproducer.
* **PASS_TO_PASS** tests guard behaviour the buggy package already gets right and
  must pass on **both** the broken and gold references — the broken variant is
  "valid" only if it fails ≥1 F2P **and** still passes every P2P (proving the
  fault is localised and the grader discriminates a real fix from a superficial one).
* The grader imports **≥2 modules** of the package (via `gu.load_module`) and runs
  integration tests that span them, so deleting the package and re-implementing a
  single file does not satisfy the contract.

### compositional
Modelled on **BigCodeBench**: one function (or small module) that must **compose
≥2 libraries** from the pinned set (e.g. `pandas`+`scipy`+`matplotlib`,
`networkx`+`pyyaml`+`jinja2`) under a precise, docstring-style contract.

* ≥5 tests at high branch coverage including **every documented exception path**,
  asserted by **type** (`pytest.raises(SpecificError)`) — never by message.
* Any statistical/numeric step is checked against precomputed ground truth with
  `gu.close`; conclusions (not exact p-values) where library drift applies.
* A **surface-form** constraint (`gu.source_uses`) requires the intended library
  call, so a hand-rolled re-implementation that lands in tolerance does not pass.
* The broken reference satisfies the easy constraints (happy path) but fails a
  harder one (a wrong branch, a wrong exception type, or a wrong composed result).

### competitive
Modelled on **LiveCodeBench / APPS**: contest-level algorithmic problems, harder
than `algorithmic` and **contamination-resistant** (original or non-trivially
twisted — novel tie-breaking / output format / constraints that invalidate a
memorised canonical solution; `created` date recorded for temporal filtering).

* **Correctness (hard gate):** ≥10 cases incl. empty/singleton/boundary plus
  **adversarial inputs** that defeat a specific wrong approach (e.g. greedy where
  DP is required), tagged `adversarial_` in the test id.
* **Complexity (hard gate, by feasibility):** one large input under
  `gu.time_limit`; `N` and the timeout are stated in `TASK.md`, the timeout chosen
  with **≥3× headroom** over the gold and so that the wrong-complexity solution
  takes **≥10×** longer (robust to machine-speed jitter). All random inputs use a
  **fixed, documented seed**.
* Soft `estimate_time_complexity` signal + advisory `code_quality`, as in
  `algorithmic`.

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

## 7. Independent-oracle grounding & mutation-seeded corpora

A benchmark whose gold solutions are AI-authored cannot, on its own, prove those
golds are correct (the author cannot exceed their own ceiling). Two mechanisms
address this for the `swe_bench` and `competitive` tasks (`swe01`–`swe04`,
`cp01`–`cp04`); both are produced at **authoring time** and replayed
deterministically at grade time.

**(a) Independent oracle (ground truth not derived from the gold).** Each task's
"expected" answers are decided by a reference that shares no code with the gold,
and the gold is *cross-validated* against it (`build_corpus` asserts
`gold(x) == oracle(x)` on every kept input, over thousands of probes). Three
honestly-distinguished tiers:

* **True external engine** — a trusted stdlib/third-party implementation:
  `cp03` uses Python `re` (DOTALL, `fullmatch` per window); `swe03` uses `jinja2`
  (`ChainableUndefined`). The gold is validated against software written by
  someone else.
* **Structurally-independent brute force** — a different algorithm, same author:
  `cp01` (O(n·q) array), `cp02` (2ⁿ subset enumeration), `cp04` (all-pairs
  Dijkstra) cross-check the clever O(n log n) / O(n) golds.
* **Independent reference + metamorphic relation** — `swe01`/`swe02` use a
  from-scratch reference; `swe04` adds the oracle-free relation `dim((a/b)·b) ==
  dim(a)`, which a wrong-division gold cannot satisfy (this breaks the
  same-author blind-spot risk a self-written reference would share).

**(b) Mutation-seeded corpus (tests target real failure modes).** Wrong solutions
are harvested from AST mutation operators applied to the gold (ROR / AOR / boolean
/ int±1), the task's own `__broken` reference, and a few hand-written
common-mistake implementations. The committed corpus
(`expected/mutation_corpus.json`, hidden — `expected/` is never copied to the
agent workspace) is the set of inputs that make ≥1 wrong solution disagree with
the gold; mutants no input can kill are reported as likely-equivalent and excluded
from the kill rate. The grader replays this corpus as `test_mutation_corpus`, so a
subtly-incorrect candidate that slips past the curated tests is caught by an
*empirically-discovered* killing input rather than a guessed one.

For the three competitive tasks whose `__broken` is correct-but-slow (`cp01`,
`cp03`, `cp04`), the corpus targets **correctness** mutants while the existing
time gate still discriminates the complexity-broken reference; where `__broken` is
itself output-wrong (`cp02`, `swe01`–`swe04`) the corpus also fails it on many
inputs, sharply increasing discrimination. Tooling: `experiment_mihaco/
_mutation_seed.py` (toolkit) and `experiment_mihaco/mutation_gen/gen_*.py`
(per-task generators); citations to the originating external problems/bugs live in
each `task.json` `source`/`oracle` field (hidden, not in `TASK.md`, to avoid
adding contamination signal).
