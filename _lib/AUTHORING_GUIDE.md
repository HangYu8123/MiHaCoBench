# PyBench task-authoring contract (read fully before writing a task)

You are authoring ONE benchmark task. Mirror the working exemplar exactly:

* `benchmark/tasks/easy/e01_csv_pulse/` — TASK.md, task.json, grader/test_e01.py
* `benchmark/_solutions/easy/e01_csv_pulse/` — gold `solution.py`
* `benchmark/_solutions/easy/e01_csv_pulse__broken/` — broken variant

## Files you MUST create (absolute paths)

```
benchmark/tasks/<CATEGORY>/<TASK_ID>/TASK.md          # prompt + EXACT contract (the only thing the agent sees)
benchmark/tasks/<CATEGORY>/<TASK_ID>/task.json        # manifest (copy e01's shape; set fields below)
benchmark/tasks/<CATEGORY>/<TASK_ID>/grader/test_<SHORT>.py
benchmark/tasks/<CATEGORY>/<TASK_ID>/data/...         # ONLY if committed inputs are needed (data_analysis/ml/long_horizon)
benchmark/tasks/<CATEGORY>/<TASK_ID>/expected/...     # ONLY if precomputed ground-truth fixtures are needed
benchmark/_solutions/<CATEGORY>/<TASK_ID>/...         # GOLD reference (the full working solution)
benchmark/_solutions/<CATEGORY>/<TASK_ID>__broken/... # broken variant (same filenames, planted defect(s))
```

`task.json` fields: `id` (=TASK_ID), `category`, `title`, `weight` (from RUBRIC.md),
`packages` (list), `entrypoints` (module + callables + cli bool), `grader`
(relative path e.g. `grader/test_xx.py`), `steps` (int for long_horizon else null),
`complexity_target` (e.g. "O(n)" for algorithmic else null), `created` "2026-06-15".

## The grader API (import this; do NOT reinvent)

```python
from _lib import grading_utils as gu
CATEGORY, TASK_ID = "<category>", "<task_id>"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)   # resolves gold OR candidate via env — never hard-code
fn  = gu.load_callable(SOL, "solution.py", "name") # import by file path
mod = gu.load_module(SOL, "models.py")             # multi-file solutions
proc = gu.run_cli(SOL, [args...], timeout=30)      # subprocess; sets MPLBACKEND=Agg, PYTHONHASHSEED=0
gu.close(a, b, rtol=1e-3)                           # float compare
gu.png_is_valid(path); gu.count_valid_pngs(dir)    # plot validation (Pillow)
gu.time_limit(seconds) / gu.run_within(s, fn, *a)  # HARD complexity gate (large input + tight timeout)
gu.measure_runtime(make_input, run, sizes); gu.estimate_time_complexity(timings)  # SOFT signal
gu.within_one_tier(measured, target); gu.measure_peak_memory(fn, *a)
gu.sha256_file(p); gu.sha256_bytes(b); gu.canonical_json_bytes(obj)  # long_horizon provenance
gu.source_uses(SOL, ["scipy.stats.ttest_ind"])     # data_analysis surface-form constraint
gu.code_quality_report(SOL)                         # advisory only — print, never assert
```

## Hard rules (from RUBRIC.md — non-negotiable)

1. **Grader integrity:** the grader MUST pass on the gold reference (every test) and
   MUST fail on the broken reference (≥1 test fails). Verify both before you finish.
2. Test the **public contract only** — never internal names/structure/import order.
3. ≥6 tests for easy/ml; ≥8 for algorithmic (incl. empty/singleton/boundary/adversarial).
4. Floats via `gu.close`/tolerance, never `==`. Assert exception **types**, not messages.
5. TASK.md must state the EXACT output contract (file names, JSON keys, dtypes, signatures).
6. Determinism: fixed seeds; committed datasets (never generate random data in the grader).
7. Use only packages in `benchmark/requirements.txt`. Domain-specific entrypoint names
   (e.g. `compute_cohort_retention`, not `solve`). Add a `code_quality` advisory test.

## Category specifics

* **easy** — single file `solution.py`, stdlib + ≤4 listed packages, ~100 LOC gold.
* **complex** — multi-file gold (~1000 LOC), multiple classes, ≥2 packages incl. the
  large one named in the spec. Grade IN-PROCESS: in-memory SQLite for SQLAlchemy,
  synthetic WSGI `environ` for web. Per-entrypoint tests for method-level partial credit.
* **data_analysis** — commit dataset to `data/`; precompute ground truth to
  `expected/<id>.json` by RUNNING your gold; grader checks results.json keys within
  tolerance + p-value CONCLUSION (reject/not at α=0.05) + `gu.source_uses` for the
  intended stat fn + `gu.png_is_valid` for each required PNG.
* **algorithmic** — correctness (≥8) + ONE large-input test under `gu.time_limit`
  (the real complexity gate; put exact N + timeout in TASK.md) + a `soft_complexity`
  test using the estimator (only fail if >2 tiers worse) + advisory code_quality.
  For `edit_distance`, add a `tracemalloc` sub-quadratic memory check.
* **long_horizon** — gold is one `solution.py` dispatching on `--step K --in <prev> --out <out>`.
  Step K reads ONLY step K-1's artifact and writes JSON containing its result AND
  `provenance` = `gu.sha256_file(prev)`. Grader runs steps in order, verifies the
  provenance chain, compares each step's output to the canonical chain, emits one
  test per step + a final cumulative test. Errors must cascade.
* **ml** — solution exposes `train(X,y)`+`predict(X)` (or `fit_predict` for clustering).
  Grader does its OWN split on the committed/`sklearn`-bundled dataset, checks held-out
  threshold, AND a mislabelled-holdout-near-chance anti-leakage sanity. Fixed seeds.

## Finish criterion

Run (from repo root):
```
python benchmark/run_benchmark.py --self-check --task <TASK_ID>
```
It must print `[PASS] ... gold N/N  broken k/N` with k<N. Only then are you done.
