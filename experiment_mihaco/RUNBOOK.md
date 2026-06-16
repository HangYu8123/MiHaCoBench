# HarnessFlow × MiHaCoBench — Full-Suite Runbook

How the full 35-task × 3-arm experiment is run, and **how to run the `general`
arm later and integrate its results** (per the current scope decision: run
`naive` + `fast` now, keep `general` runnable later).

## Arms (model held constant = Sonnet 4.6; orchestrator = Opus 4.8)

| Arm | Harness | Subagents / task |
|---|---|---|
| `naive` | none (plain prompt) | 1 implementer |
| `fast` | `claudecode_token_effective_workflow/code.instructions.md` | devil ∥ research → implementer = **3** |
| `general` | `claudecode_workflow/code.instructions.md` | 3 analysts → senior → devil ∥ research → implementer → QA (+revise if blocking) = **7–8** |

Each generation subagent gets **only its task's `TASK.md`** (spec-only isolation,
instruction-enforced) and **writes its solution files directly** to
`cand_<arm>/<category>/<task_id>/`. No gold/grader/expected files are read; no
library "gotcha" hints are injected by the orchestrator — so arm differences
reflect harness *process*, not orchestrator help.

The 6 pilot tasks (the `*01` of each category) were generated in the earlier
pilot and are **reused** unchanged; this run generates the other **29 tasks**.

## Apparatus files

| File | Role |
|---|---|
| `_gen_workflow.js` | The generation Workflow. Self-contained: `DEFAULT_ARMS`, the 29 task ids, and repo paths are embedded (the Workflow `args` channel is unreliable — see "args wiring" below). |
| `grade_all.py` | Full-35 grader for given arms. Sequential per arm, copies `results.json` → `results/eval_<arm>_full.json` immediately (no overwrite race), and pre-checks each task for MISSING_DIR / NO_PY_FILES / COMPILE_ERROR. |
| `_tokscan.py` | Per-arm token attribution from the Workflow's `agent-*.jsonl` transcripts (classifies by role marker in each prompt). |
| `consolidate.py` | Merges pilot + full eval JSONs + tokens into `results/consolidated_full.json` (built when reporting). |
| `_distribute.py` | Legacy pilot helper (consumed a single workflow-return JSON). **Not used** in the full run — agents write to disk directly, avoiding the large-return truncation risk. |
| `_grade.py` | Legacy pilot grader — hardcodes only the 6 pilot tasks. **Do not use** for the full run; use `grade_all.py`. |

## Run order (naive + fast — done now)

```bash
# 1. Generate (background Workflow, Sonnet subagents). DEFAULT_ARMS = ['naive','fast'].
#    Invoked via the Workflow tool with {scriptPath: ".../experiment_mihaco/_gen_workflow.js"}.
# 2. Grade the full 35 per arm:
python3 experiment_mihaco/grade_all.py naive fast
# 3. Token attribution from the run's transcript dir:
python3 experiment_mihaco/_tokscan.py <workflow_transcript_dir> --out experiment_mihaco/results/tokens_full.json
```

## Run the GENERAL arm later, then integrate

1. **Generate general** — edit `_gen_workflow.js`, set:
   ```js
   const DEFAULT_ARMS = ['general']
   ```
   then re-invoke the Workflow tool:
   `Workflow({scriptPath: ".../experiment_mihaco/_gen_workflow.js"})`.
   It writes only into `cand_general/<cat>/<id>/` for the 29 tasks; `naive`,
   `fast`, and all pilot dirs are untouched. (`runGeneral` is already defined and
   was validated by the pilot's 8-subagent general pipeline.)
2. **Grade general** (full 35):
   ```bash
   python3 experiment_mihaco/grade_all.py general
   ```
   → writes `results/eval_general_full.json` (sequential, so no clash with the
   already-written naive/fast eval files).
3. **Token attribution** for the general run's transcript dir:
   ```bash
   python3 experiment_mihaco/_tokscan.py <general_workflow_transcript_dir> --out experiment_mihaco/results/tokens_general.json
   ```
4. **Integrate** — re-run `consolidate.py` (it picks up whichever
   `eval_<arm>_full.json` files exist) and regenerate `COMPARISON_LOG_FULL.md`
   with the third column filled in. No naive/fast re-run needed.

## Apparatus fixes applied (vs the pilot)

* **args wiring**: the Workflow `args` channel delivered an empty object, so the
  task list / paths are embedded directly in `_gen_workflow.js`.
* **direct-to-disk writes**: implementers write files themselves and return only
  a small manifest — eliminates the ~800 KB single-return truncation risk that
  would silently drop multi-file `complex` solutions.
* **grading**: `grade_all.py` grades all 35 (not the 6-task `_grade.py`) and
  copies `results.json` per arm before the next arm overwrites it.

## "Do not fix" policy

Errors in **generated candidate code** (compile errors, missing files, failing
grader tests, timeouts) are **logged** to `results/ERROR_LOG.md`, never fixed —
they seed later code-fix tasks. Errors in the **apparatus** (this workflow,
graders, scripts) are fixed, since they are not the experiment's variable.
