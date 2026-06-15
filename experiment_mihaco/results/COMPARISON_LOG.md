# HarnessFlow × MiHaCoBench — Comparison Log (Pilot)

**Date:** 2026-06-15
**Harness:** HarnessFlow `code.instructions.md` workflows, driven via the `exec` (fast) workflow, Claude Code CLI
**Orchestrator model:** Claude **Opus 4.8** (this session)
**Subagent model (held constant across every arm):** Claude **Sonnet 4.6**
*(model parity confirmed: every spawned subagent self-reported `claude-sonnet-4-6`)*

This is a **pilot**: **one task from each of the six MiHaCoBench categories** (6 tasks),
each solved independently under **three harness arms**, then graded by the benchmark's
own independent graders (`run_benchmark.py --candidate-root`).

| Arm | Workflow | Process (subagents / task) |
|---|---|---|
| **naive** | none (plain prompt) | 1 implementer, no harness |
| **fast** | `claudecode_token_effective_workflow/code.instructions.md` | devil ∥ research → implementer = **3** |
| **general** | `claudecode_workflow/code.instructions.md` | 3 analysts → senior synth → devil ∥ research → implementer → QA (+revise if blocking) = **8** |

Tasks (one per category): `e01_csv_pulse` (easy, w1), `a01_find_pair_indices`
(algorithmic, w2), `d01_ab_test_report` (data_analysis, w3),
`m01_tabular_classification` (ml, w3), `c01_job_queue_sqla` (complex, w5),
`lh01_two_step_tally` (long_horizon, w1).

---

## 1. Methodology

- **Same model everywhere.** All 72 generation subagents ran on **Sonnet 4.6**; only the
  *harness* (process) varies between arms. The orchestrator was **Opus 4.8**.
- **Independent, pre-existing graders.** Each task is scored by MiHaCoBench's own
  `grader/test_*.py`, written against the published `TASK.md` contract — not against any
  arm's code. Grader integrity was re-verified up front: `--self-check` passed on all 6
  (gold PASS / broken FAIL), and a **gold-as-candidate** dry run scored **6/6 strict,
  weighted 1.0**, validating the full candidate-root grading path before any arm was graded.
- **Spec-only isolation.** Every generation subagent was given **only** its task's
  `TASK.md` and explicitly forbidden from reading any `grader/`, `_solutions/`,
  `expected/`, or other task/arm directory. Solutions were returned as structured file
  contents and written to per-arm candidate roots by the orchestrator. **No gotcha-fixes
  were injected into prompts** — so arm differences reflect harness *process*, not
  orchestrator hints. (Isolation is instruction-enforced, not sandboxed — see Caveats.)
- **Token measurement is real, not estimated.** Each subagent transcript's per-turn
  `usage` was summed and attributed to an arm by a distinctive role marker in its prompt
  (`experiment_mihaco/_tokscan.py`). All 72 transcripts classified cleanly (0 unknown).
- **Grading accumulation.** `run_benchmark.py` overwrites `results.json` on every
  `evaluate()` call; `experiment_mihaco/_grade.py` reads it immediately after each
  per-task run and accumulates, so no task result is lost. (Bug surfaced by the Step-3
  Devil's-Advocate review.)

### Caveats (read before trusting any single number)
- **n = 1 build per arm per task.** No replicas. Agentic builds have large documented
  run-to-run variance (token cost up to ~10×; outcome can flip on an ambiguous spec).
  Every per-task and per-arm difference here is **a single sample — exploratory, not
  statistically significant.**
- **Isolation is instruction-only.** Subagents *could* technically read hidden files; we
  rely on the prompt prohibition and flag suspicious results. Mitigation check: **no arm's
  solution is byte-identical to the gold reference**, and the one perfect arm's code uses
  independent structure — no contamination signal found.
- **Concurrent arms / shared prompt cache.** All arms ran concurrently inside one
  workflow; cache-read accounting reflects that. Cache reads are ~78% of total tokens.
- **Orchestration excluded.** The Opus 4.8 coordinator's own tokens (reading instructions,
  launching the workflow, grading) are not attributed to any arm.

---

## 2. Outcome quality (benchmark score) — the headline

| Arm | strict | weighted-partial | failing test |
|---|---|---|---|
| **naive** | **6 / 6** | **1.0000** | — |
| **fast** | 5 / 6 | 0.9744 | `c01::test_fail_retries_then_failed` |
| **general** | 5 / 6 | 0.9744 | `c01::test_fail_retries_then_failed` |

Per-category strict pass (all arms scored 1.0 partial except where noted):

| Category (task, weight) | naive | fast | general |
|---|---|---|---|
| easy (e01, w1) | ✅ 11/11 | ✅ 11/11 | ✅ 11/11 |
| algorithmic (a01, w2) — O(n) 2M/5s gate | ✅ 13/13 | ✅ 13/13 | ✅ 13/13 |
| data_analysis (d01, w3) — Welch t-test + 2 PNGs | ✅ 11/11 | ✅ 11/11 | ✅ 11/11 |
| ml (m01, w3) — held-out acc > 0.92 | ✅ 8/8 | ✅ 8/8 | ✅ 8/8 |
| complex (c01, w5) — SQLAlchemy 2.0 job queue | ✅ 13/13 | ⚠️ **12/13** | ⚠️ **12/13** |
| long_horizon (lh01, w1) — sha256 provenance | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 |

**All three arms cleared the hard gates** that usually separate harnesses: the O(n)
two-million-element timing gate (a01), the held-out + anti-leakage ML threshold (m01), the
`scipy.stats.ttest_ind` surface-form + numeric-tolerance stats (d01), and the cascading
sha256 provenance chain (lh01). On 16 of 18 task-solves the result is a perfect strict pass.

### The one discriminating result — c01 retry off-by-one

`c01::test_fail_retries_then_failed`: with `max_retries=3`, after the **3rd** `fail()` the
status must be `"failed"`. The arms diverged on **when** the retry counter is compared:

- **naive — PASS:** increments `attempts`, *then* compares — 3rd fail → `attempts=3`,
  `3 < 3` is False → `"failed"`. ✅
- **fast & general — FAIL:** compare `attempts < max_retries` **before** incrementing —
  3rd fail → `2 < 3` True → increment, `"pending"`; a *4th* fail would be needed to mark
  failed. ❌ Both arms' docstrings explicitly state the check is done "before incrementing."

The `fail()` contract is genuinely ambiguous about pre- vs post-increment comparison; the
hidden test enforces the gold (post-increment) reading. On this single run, the **more
deliberative arms reasoned themselves into the literal-but-wrong interpretation**, while
the naive arm used the common increment-then-compare idiom that happens to match. This is a
real cautionary data point — *more process did not help resolve an ambiguous spec, and
here slightly hurt* — but at **n=1 it is within expected variance**, not evidence that the
harness is worse. (No solution was hand-patched; this is the raw measured outcome.)

---

## 3. Cost (real token usage, all 6 tasks per arm)

| Metric | naive | fast | general |
|---|---:|---:|---:|
| Subagents | 6 | 18 | 48 |
| **TOTAL tokens** | **383,407** | **1,458,721** | **4,039,506** |
| × naive | 1.00× | **3.80×** | **10.54×** |
| output tokens | 12,975 | 27,247 | 68,189 |
| cache-read tokens | 267,003 | 1,137,393 | 3,151,537 |
| turns | 25 | 82 | 216 |

- The **fast** harness cost **~3.8×** the no-harness baseline; **general ~10.5×**. Token
  cost scales with subagent count (6 → 18 → 48). These ratios track the earlier ShapeLab
  experiment (fast 3.7×, general 7.4×); general is higher here because its analyst/senior/QA
  roles re-read each task's context across 6 separate tasks.
- **Cache reads dominate (~78%)** — the harness premium is overwhelmingly extra subagents
  re-reading context, not extra generation (output tokens grow only ~2.1× / ~5.3×).

### Quality-normalized cost (this pilot)

| | naive | fast | general |
|---|---:|---:|---:|
| weighted-partial | **1.0000** | 0.9744 | 0.9744 |
| tokens per weighted-point | **383k** | 1.50M | 4.15M |

On these six well-specified tasks, the extra ~1.1M (fast) / ~3.7M (general) tokens bought
**no measured score improvement** — and coincided with one shared regression on an
ambiguous spec clause.

---

## 4. Bottom line

| Question | Answer (this pilot, n=1) |
|---|---|
| Did the pipeline run end-to-end with no infra errors? | **Yes** — after fixing 2 apparatus bugs (workflow `args` wiring; `results.json` overwrite). |
| Are the deliverables good? | **Yes** — 18/18 solutions compile and run; **16/18 task-solves are perfect strict passes**; the 2 misses are one shared, well-understood off-by-one. |
| How much more does **fast** cost vs no harness? | **~3.8× tokens.** |
| How much more does **general** cost vs no harness? | **~10.5× tokens.** |
| Did more harness buy more score here? | **No** — naive 6/6 (1.0) ≥ fast/general 5/6 (0.974). |
| Why? | The tasks are well-specified and within Sonnet 4.6's single-shot ability, so the baseline already aces them; the only ambiguous clause (c01 retry) was *mis-resolved* by the deliberative arms — plausibly noise at n=1. |

**Interpretation.** For well-specified tasks a strong model already solves in one shot, the
**no-harness baseline is dramatically cheaper and at least as good** — consistent with the
ShapeLab finding that harness value concentrates in *robustness on under-specified / edge-case
work*, not headline pass-rate. This pilot validates the full HarnessFlow×MiHaCoBench
apparatus end-to-end and is the basis for scaling to the full 35-task suite **with ≥3
replicas per arm** so the n=1 variance (which produced the only score difference here) can be
averaged out.

*Raw data: `results/eval_{naive,fast,general}.json`, `results/tokens.json`,
`results/consolidated.json`. Solutions: `cand_{naive,fast,general}/<category>/<task_id>/`.*
