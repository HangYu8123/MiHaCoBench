# MiHaCoBench Simplification Proposal — trim the dead weight, add tasks the agent will fail

**Date:** 2026-06-17 · **Status:** proposal for review (no tasks deleted, none authored yet) ·
**Scope decided:** hardness goal = *tasks the agent will actually fail*; trim depth = *Moderate*;
deliverable = *analysis + specs*.

This document answers three asks: **(1)** which tasks are too simple to keep, **(2)** what harder tasks to
add, **(3)** what current LLM coding agents actually fail at (web research, mid-2026), used to ground (2).

---

## Why this change

MiHaCoBench scores **coding harnesses** (naive / fast / skill at a fixed model), but the suite's own
evaluation data shows it **barely discriminates**:

- In the full 79-task run ([`results/FULL_79_NAIVE_FAST_SKILL.md`](results/FULL_79_NAIVE_FAST_SKILL.md)),
  **72 of 79 tasks are a 3-way tie** — every arm strict-passes. Only 7 tasks ever diverge, and only
  **`cb08_cursor_paginate`** is a clean discriminator (naive 0.44 vs skill 1.00).
- The expansion report ([`results/NEW_TASKS_DISCRIMINATION.md`](results/NEW_TASKS_DISCRIMINATION.md))
  already proved *why*: **spec-density traps don't separate harnesses** (a careful frontier model just reads
  the spec — naive scored 14/14), and **textbook complexity gates don't either** (the model knows Fenwick
  trees / binary-search-on-answer). The one mechanism that worked was **subtle boundary ambiguity**
  (`cb08`).

So the suite is correct (graders are valid) but **flat** — it spends most of its 79 tasks confirming a
frontier model can do things it can already do. The fix is to remove repetition/trivia and replace it with
tasks at the agent's real failure frontier.

**The one hard constraint that shapes every "harder" task:** the integrity invariant
(`run_benchmark.py --self-check`) requires every task to ship a **working gold reference** (grader passes
gold) and a **broken reference** (grader fails broken). So "a task the agent will fail" cannot mean
*unsolvable* — it must be **solvable in principle (gold exists) but sit at or past the agent's failure
frontier**, so the agent-under-test fails to *re-derive* the solution from the spec.

---

## What "hard enough to fail" means (research-grounded)

External research (mid-2026) on where frontier coding agents break — the failure modes worth designing for:

| Failure mode | Evidence (SOTA performance) | Why the agent fails |
|---|---|---|
| **Observation-heavy algorithms** | LiveCodeBench Pro **Hard ≈ 0%** even for frontier models; Med drops to ~10% | Needs a *non-obvious insight* (a property to prove), not a named algorithm. Models pick a plausible-but-wrong approach. |
| **Long-horizon cumulative-state** | HORIZON / "Long-Horizon Task Mirage"; SWE-EVO ≈ **25%** | Each step is *locally valid* but violates a *global* invariant; agents lack cumulative-state awareness (the "storage-exhaustion" pattern). |
| **Sustained cross-module evolution** | SWE-bench **Pro ≈ 40–45%**; SWE-EVO ≈ 25% (vs ~73% on Verified) | New feature must reconcile an invariant enforced in *another* module; agent implements it in isolation. |
| **Numerical stability** | classic "knows the concept, makes the error" | Reaches for the textbook formula (`E[x²]−E[x]²`, etc.) that catastrophically cancels on adversarial input. |
| **Subtle boundary ambiguity** | the proven `cb08` mechanism in *this* suite | Spec is precise but a hasty reading drops/duplicates a row at a boundary. |

Saturated benchmarks to **avoid imitating**: HumanEval / MBPP (>95%), and SWE-bench **Verified** (88–95%
SOTA, heavy contamination — ~33% solution leakage; OpenAI retired it in early 2026). Sources in the appendix.

**Design principle:** a new task earns its place only if it is **empirically failed by at least one arm**
when run. Verify (below) rather than assume difficulty.

---

## Part 1 — Removal shortlist (Moderate trim: 17 tasks, 79 → 62)

Removal rule: a task is a cut candidate when it **(a)** 3-way-ties in every recorded run (zero
discrimination) **AND (b)** is either *redundant with a sibling* or *conceptually trivial*. Tasks kept as a
deliberate "baseline competence" control or for unique skill coverage are **not** cut.

| Cut | Category | Count | Rationale | Kept for coverage |
|---|---|---:|---|---|
| `lh02,lh04,lh06,lh07,lh08,lh09` | long_horizon | 6 | **Biggest redundancy in the suite.** `lh01–lh10` are the *same* mechanism (deterministic transform chain) at lengths 2,4,…,20. All strict-pass everywhere. Keep a short/medium/long ladder only. | keep `lh01`(2), `lh03`(6), `lh05`(10), `lh10`(20), `lh11`, `lh12` |
| `e02_ini_parser`, `e05_tiny_template`, `e04_roman_ledger` | easy | 3 | "Baseline competence" needs ~3 controls, not 6; these three are the most standard. | keep `e01`, `e03`, `e06`(semver trap) |
| `dbg03_lru_cache`, `dbg04_paginate`, `dbg05_group_tally` | debug | 3 | Single-file planted-bug tasks that always pass; `swe_bench` already covers fault-localization at higher fidelity (multi-file). | keep `dbg01,02,06,07` (incl. the `dbg07` boundary trap) |
| `m03_clustering`, `m04_dimreduction` | ml | 2 | Standard sklearn calls, always pass; classification/regression/text/multiclass keep ML coverage. | keep `m01,m02,m05,m06` |
| `d02_sales_trend`, `d03_customer_segments` | data_analysis | 2 | Most generic of the 8; the statistical *traps* (`d05,d07,d08`) carry the category's signal. | keep `d01,d04,d05,d06,d07,d08` |
| `a01_find_pair_indices` | algorithmic | 1 | Two-sum, weight 2, the explicit "easy" rung — trivial for any frontier model. | keep `a02–a09` |

**Net:** 79 → **62 tasks**. Every category survives; the cuts remove repetition and trivia, not coverage.

> Before deleting, re-confirm each cut task is still a 3-way tie in the latest grade (cheap:
> `experiment_mihaco/grade_all.py`), so we never cut something that started discriminating.

---

## Part 2 + 3 — Specs for new hard tasks (the agent should fail these)

Seven authorable specs, each mapped to a research-backed failure mode and modeled on the suite's own
conventions (`cb08` for boundary tasks; [`_lib/AUTHORING_GUIDE.md`](../_lib/AUTHORING_GUIDE.md) for the
gold/broken/grader contract; competitive tasks get an **independent oracle + mutation corpus** per RUBRIC
§7). Each spec states the **failure mechanism** (why the agent gets it wrong), a **gold approach**, a
**broken variant**, and the **grader/gate**.

### A. Observation-heavy algorithm — the near-0% regime

**NT-1 · `competitive/cp07_path_xor_sum` (weight 8).**
Sum, over all unordered node pairs in a weighted tree (n ≤ 2·10⁵), of the XOR of edge weights on the path,
mod 1e9+7.
- **Failure mechanism:** the obvious "enumerate all paths" is O(n²) and **times out** on the gate; the
  intended O(n·B) needs the *non-obvious observation* that XOR is bit-independent — per bit, count pairs
  whose path has an **odd** number of set-bit edges via a subtree-parity DFS. This is observation-heavy
  (LiveCodeBench-Pro-Hard style), not a named algorithm; models pick a plausible wrong reduction.
- **Gold:** per-bit subtree DFS, `cnt_odd * cnt_even` pairs × 2^bit. **Broken:** counts *ordered* pairs
  (2× off) / drops the 2^bit weight.
- **Grader:** brute O(n²) **independent oracle** on small random trees + **hard `gu.time_limit` gate** at
  n=2·10⁵ + `expected/mutation_corpus.json` (per `mutation_gen/gen_cp03.py` pattern).

**NT-2 · `competitive/cp08_min_unstable_partition` (weight 8).**
Partition an array into the fewest contiguous segments such that no segment's (max−min) exceeds K — but the
*scored* twist is returning the lexicographically-smallest set of cut indices among all minimum partitions.
- **Failure mechanism:** greedy "extend while feasible" gets the *count* right but the *lex-smallest cuts*
  wrong; the correct solution needs a second observation (a monotone-deque feasibility check + a DP/greedy
  that proves the lex choice). Two coupled insights → models solve half. Hard gate kills O(n²) feasibility.
- **Gold:** sliding-window min/max deques + greedy-with-proof. **Broken:** plain greedy (right count, wrong cuts).
- **Grader:** brute oracle (small n, all partitions) + time gate (n=2·10⁵) + mutation corpus.

### B. Numerical stability — "knows the concept, makes the error"

**NT-3 · `compositional/cb09_streaming_covariance` (weight 4).**
Online (single-pass, bounded-memory) mean / variance / covariance over a stream of `(x, y)` pairs; compose
`numpy` (final assembly) + a pure-Python streaming accumulator.
- **Failure mechanism:** the agent reaches for `E[x²]−E[x]²` / `E[xy]−E[x]E[y]`, which **catastrophically
  cancels** when the data has a large offset (e.g. values ~1e9 with variance ~1) and **fails the tolerance**;
  gold uses Welford / co-moment updates. Documented "textbook formula" trap.
- **Gold:** Welford + running co-moment. **Broken:** sum-of-squares minus square-of-sum.
- **Grader:** adversarial large-offset streams where the naive formula loses all precision (`gu.close`,
  tight rtol) + a single-pass / memory check + small hand-checked cases.

### C. Long-horizon cumulative-state — the "locally valid, globally wrong" trap

**NT-4 · `long_horizon/lh13_quota_ledger` (weight ~6, ~12 steps).**
A multi-step allocation pipeline: step 1 fixes a **global budget** from the input; each later step allocates
a request **against the running remainder**, and the final step must reconcile to zero leftover under a
stated priority rule.
- **Failure mechanism:** redesigns long_horizon away from mechanical transforms. The trap is exactly the
  HORIZON "storage-exhaustion" pattern — a step that **re-derives the pool locally** or allocates greedily is
  *locally valid* but **overdraws the global invariant** fixed at step 1; only an agent that threads
  cumulative state through the provenance chain stays correct. Errors cascade (poisons all downstream steps).
- **Gold:** carries `remaining` + `commitments` forward in each step's `data`. **Broken:** recomputes the
  budget per step (ignores prior commitments).
- **Grader:** standard provenance chain (`gu.sha256_file`) + per-step + cumulative reconciliation test;
  an adversarial input where greedy-local overspends.

### D. Sustained cross-module evolution — SWE-EVO regime

**NT-5 · `swe_bench/swe09_evolve_ttl_index` (weight 6, ≥3 modules).**
Given a *working* mini-repo (an LRU store + a separate TTL-expiry layer + a secondary index), implement a
**new `range_invalidate(lo, hi)` feature** that must preserve an invariant the index module already relies on.
- **Failure mechanism:** SWE-EVO-style. The new feature is simple in isolation, but correctness depends on a
  contract buried in *another* module (the index assumes expiry and eviction both call `_unlink`); a naive
  implementation invalidates the range but leaves the secondary index stale → cross-feature test fails.
  Agents implement B without reconciling A's invariant (the ~25% regime).
- **Gold:** routes range-invalidation through the shared `_unlink` path. **Broken:** drops entries from the
  primary map only (stale index).
- **Grader:** FAIL_TO_PASS (the new feature) + PASS_TO_PASS (existing LRU/TTL behavior unbroken) +
  a cross-feature test that exercises invalidate-then-query-by-index. Grader imports ≥2 modules.

### E. Subtle boundary ambiguity — keep feeding the proven `cb08` family

**NT-6 · `compositional/cb10_session_window` (weight 4).**
Sessionize a sorted event stream into windows: a new session starts when the inter-event gap is **strictly
greater than** `gap` (pin `>` vs `≥` precisely), sessions carry a stable tie-break on `id`, and there is
**never a trailing empty session** — directly modeled on `cb08`'s proven-discriminating structure, new domain.
- **Failure mechanism:** identical to `cb08` — the spec pins the boundary exactly, but `≥`-vs-`>` and the
  no-trailing-empty rule are easy to misimplement in one pass. This is the one mechanism shown to split
  naive from harness in *this* suite.
- **Gold/broken/grader:** mirror `cb08` (full chain-walk equivalence: every event in exactly one session;
  broken flips `>` to `≥`).

**NT-7 · `algorithmic/a10_kth_distinct_in_window` (weight 8).**
Stream of `(query, window)`; for each, the k-th **distinct** value within a sliding window, ties and
window-boundary inclusivity pinned precisely. Hard gate forces an efficient structure.
- **Failure mechanism:** boundary ambiguity (inclusive window end, distinctness across the boundary) ×
  a complexity gate (naive recount per query is O(nq) and times out). Two coupled traps.
- **Gold:** sliding window + ordered multiset / BIT over last-occurrence. **Broken:** off-by-one window end.
- **Grader:** brute oracle (small) + correctness suite (≥8, incl. empty/singleton/all-equal) + time gate.

### Summary of additions

| Mode | New task | Cat | W | Primary reason agent fails |
|---|---|---|---:|---|
| A observation | `cp07_path_xor_sum` | competitive | 8 | non-obvious bit-decomposition insight + O(n²) gate |
| A observation | `cp08_min_unstable_partition` | competitive | 8 | two coupled insights (count + lex cuts) |
| B numerical | `cb09_streaming_covariance` | compositional | 4 | catastrophic cancellation in textbook formula |
| C cumulative-state | `lh13_quota_ledger` | long_horizon | ~6 | locally-valid step violates global invariant |
| D evolution | `swe09_evolve_ttl_index` | swe_bench | 6 | new feature breaks an invariant in another module |
| E boundary | `cb10_session_window` | compositional | 4 | `>`-vs-`≥` boundary (proven `cb08` mechanism) |
| E+gate boundary | `a10_kth_distinct_in_window` | algorithmic | 8 | window inclusivity + complexity gate |

Net if all adopted: 62 + 7 = **69 tasks**, but with a far higher share that at least one arm fails —
turning the suite from "everyone scores ~1.0" into one with real spread.

---

## Verification (how each recommendation gets validated before it's trusted)

This is analysis only; the following is what the *authoring* phase (a later, separately-approved task) must
satisfy, spelled out so the specs are executable:

1. **Grader integrity (per new task):** from repo root,
   `python run_benchmark.py --self-check --task <TASK_ID>` must print `[PASS] … gold N/N broken k/N` (k<N).
   A task that can't produce this is not valid and is dropped.
2. **"The agent actually fails" check (the whole point):** scaffold the new task to an external dir
   (`run_benchmark.py --scaffold-candidate`), run the naive and skill arms over it (the existing
   `experiment_mihaco` generators), grade with `grade_all.py`. **Keep the task only if ≥1 arm fails or
   partially fails it.** If both arms ace it, it joins the "spec-density doesn't discriminate" graveyard —
   discard or harden.
3. **Removal safety:** re-run `grade_all.py` and confirm each Part-1 cut task is still a 3-way tie in the
   latest grade before deletion.
4. **Suite still self-consistent:** full `python run_benchmark.py` (self-check all) stays green; update the
   counts in [`README.md`](../README.md) (badge + category table) and [`RUBRIC.md`](../RUBRIC.md).

---

## Research appendix — sources

- SWE-bench Verified saturation/contamination & retirement: [OpenAI — why we no longer evaluate SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), [SWE-bench leaderboard 2026](https://www.codeant.ai/blogs/swe-bench-scores), [SWE-bench Pro leaderboard](https://www.morphllm.com/swe-bench-pro)
- Still-hard / unsaturated: [LiveCodeBench Pro (olympiad-medalist analysis)](https://arxiv.org/pdf/2506.11928), [LiveCodeBench Pro leaderboard](https://llm-stats.com/benchmarks/livecodebench-pro), [AI Benchmarks 2026 & limits (Kili)](https://kili-technology.com/blog/ai-benchmarks-guide-the-top-evaluations-in-2026-and-why-theyre-not-enough)
- Long-horizon / evolution failure: [SWE-bench Pro (arXiv 2509.16941)](https://arxiv.org/pdf/2509.16941), [SWE-EVO (arXiv 2512.18470)](https://arxiv.org/html/2512.18470v5), [The Long-Horizon Task Mirage (arXiv 2604.11978)](https://arxiv.org/abs/2604.11978)
- Reasoning failure modes (counting/copying/multi-step DP): [Frontier LLMs Still Struggle with Simple Reasoning (arXiv 2507.07313)](https://arxiv.org/pdf/2507.07313)
