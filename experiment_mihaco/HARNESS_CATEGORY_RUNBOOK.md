# `harness` category — build & validation runbook

**Created:** 2026-06-18 · **Goal:** a category of tasks whose *whole point* is to
**discriminate a harness from a naive single-shot** on Opus 4.8.

Unlike the other 10 categories (which mostly 3-way-tie on frontier models — see
`results/NEW_TASKS_DISCRIMINATION.md` and the project memory), every task here is
*empirically gated* on the live agent: it ships only if **naive Opus 4.8 fails it**.

## Target composition (set by the requester, 2026-06-18)

5 tasks, split by empirical outcome:

| Bucket | n | naive Opus 4.8 | harnessed Opus 4.8 | Meaning |
|---|---|---|---|---|
| **discriminating** | 3 | FAIL | PASS | harness *adds* the win (the headline result) |
| **frontier** | 2 | FAIL | FAIL | at the agent's ceiling — even review can't recover it |

"PASS" = a **strict** pass: every grader test green (`partial == 1.0`). "FAIL" =
anything less.

## The two arms (model held constant = Opus 4.8; isolation = instruction-enforced)

Mirrors `RUNBOOK.md`'s arms, adapted to a single-task loop.

| Arm | Process | Subagents |
|---|---|---|
| **naive** | One implementer. Given **only** `TASK.md`. Writes `solution.py` in a single pass. **No** edge-case enumeration, **no** QA/review, **no** iteration. | 1 |
| **harness** | devil/edge-case analyst (fresh context, enumerates every boundary/ordering/precision trap in the spec) → implementer (spec + traps) → QA reviewer (fresh, *adversarially* tries to break the impl on edge cases) → reviser. | 3–4 |

Both arms see **only** the `TASK.md` contract — never the grader, gold, `__broken`,
or `expected/`. The *only* variable is the harness's adversarial review loop. This
is exactly the mechanism the literature says recovers the "happy-path-correct but
edge-case-broken, reviewable" code a single shot emits (Self-Refine / Reflexion /
QA-Test-Engineer role), and the same literature's caveat — review can *misread a
subtle spec and invent requirements* — is why some tasks stay FAIL for both arms.

## Design levers (how a task lands in each bucket)

All tasks are **fully specified** (the suite's design pillar): every rule is stated
in `TASK.md`. Difficulty is **constraint density + subtle interaction**, never
hidden requirements. The grader enforces the subtle invariants strictly.

* **discriminating** → **one** central subtle invariant that a focused QA pass
  reliably rediscovers (cb08 model: exclusive cursor / tie-break / no-trailing-page).
  Naive emits happy-path code that violates it; the review pass catches it.
* **frontier** → **several independent** subtle traps, or one deep trap + a tight
  scale/feasibility gate, so even an adversarial review misses ≥1 (or misreads the
  spec). A valid gold still exists — these are solvable *in principle*, just past
  what the agent recovers in-context.

## The loop (steps from the request)

1. **Search** online for harness/agentic-coding failure modes → seed concepts.
2. **Author** N candidate tasks (full package; self-check valid).
3. **Naive-solve** each with Opus 4.8 (spec-only, 1 pass) → grade.
4. If naive **passes** → exclude (or **harden** the spec/grader, step 6) — it does
   not discriminate.
5. **Loop** (back to 1/2) until 5 tasks remain that naive fails.
6. **Harden** as needed: tighten a subtle clause, add an adversarial grader case,
   or raise the scale gate — never by hiding a requirement.

Then run the **harness** arm on the survivors to split them into 3 discriminating +
2 frontier.

## Commands

```bash
# self-check ONE task (gold passes all, broken fails >=1):
python3 run_benchmark.py --self-check --task <id>

# grade a candidate arm's solution for ONE task:
PYBENCH_SOLUTION_DIR=experiment_mihaco/cand_<arm>/harness/<id> \
  MPLBACKEND=Agg PYTHONHASHSEED=0 \
  python3 -m pytest tasks/harness/<id>/grader/test_<x>.py -p no:cacheprovider -q

# whole-category self-check / scoring:
python3 run_benchmark.py --self-check --category harness
```

## Results

Empirical outcomes (naive vs harness, per task) are logged to
`experiment_mihaco/results/HARNESS_CATEGORY.md`.
