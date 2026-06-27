export const meta = {
  name: 'mihaco-fast-skill-validate',
  description: 'Validate the HarnessFlow FAST (token_effective) and SKILL workflows on a 16-task MiHaCoBench subset. Each task flows through the actual workflow pipeline (Step 2 plan -> Step 3 devil || research -> Step 5 implement), held at Sonnet 4.6, spec-only isolated, writing solution files directly to cand_<arm>/<cat>/<id>/. Topology is identical across arms; only the per-step METHODOLOGY differs (fast = generic token-effective prose; skill = community-skill methodology: writing-plans / the-fool / deep-research / executing-plans+TDD / systematic-debugging).',
  phases: [
    { title: 'fast', detail: 'plan -> devil || research -> implement (generic), 4/task', model: 'claude-sonnet-4-6' },
    { title: 'skill', detail: 'plan(writing-plans) -> the-fool || deep-research -> implement(executing-plans+TDD), 4/task', model: 'claude-sonnet-4-6' },
  ],
}

// ---- config (args optional override; embedded by default — args wiring unreliable) ----
const _A = (typeof args !== 'undefined' && args) ? args : {}
const BENCH = _A.bench_root || '/Users/hangyu/Desktop/MiHaCoBench'
const EXP = _A.exp_root || '/Users/hangyu/Desktop/MiHaCoBench/experiment_mihaco'
const ARMS = (_A.arms && _A.arms.length) ? _A.arms : ['fast', 'skill']
const MODEL = 'sonnet' // every subagent held at Sonnet 4.6
// 16-task representative subset (mode: 'code' uses the code workflow; 'debug' uses the debug workflow)
const TASKS = (_A.tasks && _A.tasks.length) ? _A.tasks : [
  { cat: 'easy', id: 'e01_csv_pulse', mode: 'code' },
  { cat: 'easy', id: 'e06_semver_order', mode: 'code' },
  { cat: 'algorithmic', id: 'a04_edit_distance', mode: 'code' },
  { cat: 'algorithmic', id: 'a08_cooldown_profit', mode: 'code' },
  { cat: 'complex', id: 'c01_job_queue_sqla', mode: 'code' },
  { cat: 'complex', id: 'c09_reactive_engine', mode: 'code' },
  { cat: 'data_analysis', id: 'd05_experiment_anova', mode: 'code' },
  { cat: 'data_analysis', id: 'd07_paired_design', mode: 'code' },
  { cat: 'long_horizon', id: 'lh12_budget_forecast', mode: 'code' },
  { cat: 'ml', id: 'm03_clustering', mode: 'code' },
  { cat: 'compositional', id: 'cb02_workflow_dag', mode: 'code' },
  { cat: 'compositional', id: 'cb08_cursor_paginate', mode: 'code' },
  { cat: 'competitive', id: 'cp05_kth_subarray_sum', mode: 'code' },
  { cat: 'debug', id: 'dbg02_resolve_order', mode: 'debug' },
  { cat: 'debug', id: 'dbg07_token_bucket', mode: 'debug' },
  { cat: 'swe_bench', id: 'swe08_money_rounding', mode: 'debug' },
]

const targetDir = (arm, t) => `${EXP}/cand_${arm}/${t.cat}/${t.id}`
const specPath = (t) => `${BENCH}/tasks/${t.cat}/${t.id}/TASK.md`

const ISO = (t) => `
SPEC-ONLY ISOLATION (STRICT):
- Read EXACTLY ONE file for the specification: ${specPath(t)}
- Do NOT read/open/list/grep any */grader/*, _solutions/*, */expected/*, or any other task directory. Solve purely from that one TASK.md.
ENVIRONMENT: Python 3.11.5, offline. Allowed imports: stdlib + { numpy, pandas, scipy, scikit-learn (sklearn), matplotlib, PIL, sqlalchemy, jinja2, networkx, yaml, joblib }. The grader sets MPLBACKEND=Agg and PYTHONHASHSEED=0 at runtime.`

const WRITE = (arm, t) => `
DELIVERABLE — write your solution to disk:
- Use the Write tool to create your complete solution file(s) in this EXACT directory (it already exists):
    ${targetDir(arm, t)}
- Create the EXACT filename(s) required by the spec's contract / "File layout" section (e.g. solution.py, or for multi-file/complex tasks the named module the contract demands). Flat layout unless the spec says otherwise. Leave NO scratch or test files behind — only the required solution module(s).
- The grader imports your files by path and checks ONLY the public contract: required entrypoint names + signatures must match the spec exactly. Make it correct, deterministic, and complexity/memory-gate compliant.
- Then return a manifest. If (and only if) the Write tool is unavailable to you, instead return the full file contents in 'files_inline'.`

const MANIFEST_SCHEMA = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' }, description: 'filenames you WROTE into the target dir' },
    files_inline: {
      type: 'array',
      description: 'ONLY if you could not use the Write tool: full contents to be written by the orchestrator',
      items: { type: 'object', properties: { name: { type: 'string' }, content: { type: 'string' } }, required: ['name', 'content'] },
    },
    notes: { type: 'string', description: 'one line: approach + (skill arm) the skill discipline you applied' },
  },
  required: ['files'],
  additionalProperties: true,
}

// ----------------------------- prompt builders ----------------------------- //
// Each builder is branched by arm ('fast' | 'skill') and mode ('code' | 'debug').
// FAST = the token_effective workflow's generic instructions.
// SKILL = the same step re-framed around the catalogued community skill's methodology
//         (skills not vendored locally -> methodology embedded inline, per the workflow's
//          "follow <skill>" instruction; this exercises skill-backed behavior, not the fallback).

function plannerP(arm, t) {
  if (t.mode === 'debug') {
    if (arm === 'skill') {
      return `You are the SKILL-harness debugger executing Step 2 (Diagnosis & Fix Plan) of the skill-backed debug workflow, via the systematic-debugging skill (obra/superpowers). Sonnet 4.6.
${ISO(t)}
The spec contains a BUGGY implementation + the failing symptom. Apply systematic-debugging discipline: (1) mentally REPRODUCE the symptom, (2) ISOLATE the smallest failing path, (3) identify the ROOT CAUSE with concrete evidence from the buggy code — do NOT guess a fix before the root cause is established. Then give a MINIMAL fix [plan] that preserves the exact public contract (FAIL_TO_PASS without breaking PASS_TO_PASS).
Return [plan] (<=400 words): root cause (with evidence) + the precise minimal change(s) + the required module filename + edge cases the fix must still satisfy. No files.`
    }
    return `You are the FAST-harness debugger executing Step 2 (Diagnosis & Fix Plan) of the token-effective debug workflow. Sonnet 4.6.
${ISO(t)}
The spec contains a BUGGY implementation + the failing symptom. Identify the most likely root cause(s) with evidence ([bug info]) and a fix [plan] that preserves the exact public contract without introducing regressions.
Return [plan] (<=350 words): root cause + minimal fix + required module filename + edge cases. No files.`
  }
  if (arm === 'skill') {
    return `You are the SKILL-harness planner executing Step 2 (Implementation Planning) of the skill-backed code workflow, via the writing-plans skill (obra/superpowers). Sonnet 4.6.
${ISO(t)}
Apply writing-plans discipline: turn the spec into a DEPENDENCY-ORDERED set of bite-sized tasks. For EACH task name: the exact file/module to touch (use the precise filename the contract demands), what to implement, and a concrete VERIFICATION check. If the contract is ambiguous on any point, briefly weigh 2-3 approaches (brainstorming) and commit to one. Explicitly call out the single hardest correctness/complexity/determinism risk and how the plan satisfies any complexity/memory gate.
Return [plan] (<=400 words): the ordered task list (file + action + verification each) + required entrypoints/signatures + the hardest risk. No files.`
  }
  return `You are the FAST-harness planner executing Step 2 (Implementation Planning) of the token-effective code workflow. Sonnet 4.6.
${ISO(t)}
Produce [plan]: the exact files/modules to create (precise names per the contract), the required entrypoints + signatures, the single hardest correctness/complexity risk and how to satisfy it, key edge cases, and determinism/IO/plot requirements.
Return [plan] (<=350 words). No files.`
}

function devilP(arm, t, plan) {
  const head = t.mode === 'debug'
    ? `Critically challenge this debug diagnosis + fix [plan] for the task.`
    : `Critically challenge this implementation [plan] for the task.`
  const focus = t.mode === 'debug'
    ? `overlooked root causes, a fix that treats the symptom not the cause, regressions to PASS_TO_PASS behavior, contract drift, off-by-one, determinism.`
    : `wrong/missing entrypoint or filename, complexity/memory-gate violation, contract mismatch, off-by-one and boundary ambiguity, library-API misuse, nondeterminism, IO/plot pitfalls, edge cases.`
  if (arm === 'skill') {
    return `You are the SKILL-harness Challenge subagent (Step 3), via the the-fool skill (Jeffallan/claude-skills) — a STRUCTURED devil's-advocate / pre-mortem. Sonnet 4.6.
${ISO(t)}
[plan]:
${plan || '(none)'}
${head} Run a pre-mortem: assume this plan SHIPS and FAILS the hidden grader; enumerate the concrete failure modes — ${focus} Report ONLY evidence-backed defects (do not manufacture problems); for each, name the fix.
Return [challenge report] (<=300 words). Do NOT write any files.`
  }
  return `You are the FAST-harness Devil's Advocate (Step 3). Sonnet 4.6.
${ISO(t)}
[plan]:
${plan || '(none)'}
${head} Assume the plan is wrong/over-engineered; surface concrete pitfalls — ${focus} Report only evidence-backed defects; for each, name the fix.
Return [challenge report] (<=300 words). Do NOT write any files.`
}

function researchP(arm, t, plan) {
  const subj = t.mode === 'debug'
    ? `the correct current library APIs / language semantics needed to fix this bug correctly (and any known-issue references for this class of bug)`
    : `the correct current library APIs / algorithms / idioms needed to implement this task (exact signatures, the right data structure for any complexity gate, correct framework usage)`
  if (arm === 'skill') {
    return `You are the SKILL-harness Online Research subagent (Step 3), via the deep-research skill (davila7/claude-code-templates) — plan -> search -> read -> synthesize a CITED brief. Sonnet 4.6.
${ISO(t)}
[plan]:
${plan || '(none)'}
Research ${subj}. Follow deep-research: if web search/fetch tools are available to you (load them via ToolSearch, e.g. WebSearch/WebFetch), run real queries and include the source URLs as proof; if no web tool is available, synthesize from your own knowledge and state "(no live web; from knowledge)".
Return [online resource] (<=300 words): the concrete APIs/idioms to use + citations. Do NOT write any files.`
  }
  return `You are the FAST-harness researcher (Step 3). Sonnet 4.6.
${ISO(t)}
[plan]:
${plan || '(none)'}
Determine ${subj}.
Return [online resource] (<=300 words): the concrete APIs/idioms to use. Do NOT write any files.`
}

function implP(arm, t, plan, devil, research) {
  const ctx = `[final plan]:
${plan || '-'}
[challenge report / must-fix]:
${devil || '-'}
[verified APIs/patterns]:
${research || '-'}`
  if (t.mode === 'debug') {
    if (arm === 'skill') {
      return `You are the SKILL-harness implementer executing Step 5 of the skill-backed debug workflow, via executing-plans + test-driven-development (obra/superpowers). Sonnet 4.6.
${ISO(t)}
${ctx}
Load the plan, review it critically, then apply TDD: (1) define the test that captures the reported bug (the symptom), (2) make the MINIMAL fix so it passes, (3) refactor — all while keeping the existing public contract (PASS_TO_PASS) intact. Self-verify against contract edge cases before finalizing.
${WRITE(arm, t)}`
    }
    return `You are the FAST-harness implementer (Step 5) of the token-effective debug workflow. Sonnet 4.6. Apply the minimal fix from the final plan; preserve the public contract; self-verify edge cases.
${ISO(t)}
${ctx}
${WRITE(arm, t)}`
  }
  if (arm === 'skill') {
    return `You are the SKILL-harness implementer executing Step 5 of the skill-backed code workflow, via executing-plans + test-driven-development (obra/superpowers). Sonnet 4.6.
${ISO(t)}
${ctx}
Load the [final plan], review it critically, then execute each planned task step-by-step. Apply TDD: derive concrete test cases from the contract and ensure your implementation satisfies them (red -> green -> refactor) BEFORE finalizing. Respect every complexity/memory gate and determinism requirement.
${WRITE(arm, t)}`
  }
  return `You are the FAST-harness implementer (Step 5) of the token-effective code workflow. Sonnet 4.6. Implement the [final plan], avoiding the must-fix pitfalls and using the verified APIs. Respect complexity/memory gates and determinism.
${ISO(t)}
${ctx}
${WRITE(arm, t)}`
}

// ----------------------------- per arm-task pipeline ----------------------------- //
async function runArm(arm, t) {
  // Step 2 — plan (spec-only isolated)
  const plan = await agent(plannerP(arm, t), { label: `${arm}:plan:${t.id}`, phase: arm, model: MODEL })
  // Step 3 — devil || research (parallel, as the workflow prescribes)
  const [devil, research] = await parallel([
    () => agent(devilP(arm, t, plan), { label: `${arm}:devil:${t.id}`, phase: arm, model: MODEL }),
    () => agent(researchP(arm, t, plan), { label: `${arm}:research:${t.id}`, phase: arm, model: MODEL }),
  ])
  // Step 5 — implement + write (spec-only isolated, returns small manifest)
  const r = await agent(implP(arm, t, plan, devil, research), { label: `${arm}:impl:${t.id}`, phase: arm, model: MODEL, schema: MANIFEST_SCHEMA })
  return {
    arm, cat: t.cat, id: t.id, mode: t.mode, subagents: 4,
    files: (r && r.files) || [], files_inline: (r && r.files_inline) || [], notes: (r && r.notes) || '',
  }
}

const jobs = []
for (const arm of ARMS) for (const t of TASKS) jobs.push({ arm, t })
log(`Validating fast vs skill: arms=[${ARMS.join(',')}], tasks=${TASKS.length} -> ${jobs.length} arm-tasks (Sonnet 4.6, 4 subagents/arm-task: plan -> devil||research -> impl)`)

const results = (await parallel(
  jobs.map((j) => () =>
    runArm(j.arm, j.t).catch((e) => ({ arm: j.arm, cat: j.t.cat, id: j.t.id, mode: j.t.mode, subagents: 0, files: [], files_inline: [], error: String((e && e.message) || e) }))
  )
)).filter(Boolean)

const produced = results.filter((r) => !r.error && ((r.files && r.files.length) || (r.files_inline && r.files_inline.length))).length
log(`Done: ${produced}/${results.length} arm-tasks produced >=1 file.`)
return { arms: ARMS, tasks: TASKS.length, results }
