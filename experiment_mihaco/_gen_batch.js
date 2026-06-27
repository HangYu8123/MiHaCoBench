export const meta = {
  name: 'mihaco-batch-gen',
  description: 'Token-budget-friendly BATCH generator for MiHaCoBench. Runs exactly the (arm,task) jobs passed via args.jobs — used to generate fast/skill (and if needed naive) ~10% of tasks at a time so a single session stays under its token limit. Sonnet 4.6, spec-only isolated, writes solutions directly to cand_<arm>/<cat>/<id>/. naive=1 implementer/task; fast/skill=plan -> devil||research -> implement.',
  phases: [
    { title: 'naive', detail: '1 one-pass implementer/task', model: 'claude-sonnet-4-6' },
    { title: 'fast', detail: 'plan -> devil||research -> implement (generic)', model: 'claude-sonnet-4-6' },
    { title: 'skill', detail: 'plan -> devil||research -> implement (community-skill methodology)', model: 'claude-sonnet-4-6' },
  ],
}

const _A = (typeof args !== 'undefined' && args) ? args : {}
const BENCH = _A.bench_root || '/Users/hangyu/Desktop/MiHaCoBench'
const EXP = _A.exp_root || '/Users/hangyu/Desktop/MiHaCoBench/experiment_mihaco'
const MODEL = 'sonnet'
// args.jobs is UNRELIABLE in this harness (delivers empty) — so the batch is EMBEDDED
// here and edited per batch (driven by _batch_log.py's NEXT_BATCH_JOBS output).
const BATCH_JOBS = [
  { arm: 'skill', cat: 'long_horizon', id: 'lh11_index_build', mode: 'code' },
  { arm: 'fast', cat: 'long_horizon', id: 'lh12_budget_forecast', mode: 'code' },
  { arm: 'skill', cat: 'long_horizon', id: 'lh12_budget_forecast', mode: 'code' },
]
const JOBS = (_A.jobs && _A.jobs.length) ? _A.jobs : BATCH_JOBS

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
    files: { type: 'array', items: { type: 'string' } },
    files_inline: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, content: { type: 'string' } }, required: ['name', 'content'] } },
    notes: { type: 'string' },
  },
  required: ['files'],
  additionalProperties: true,
}

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
  const head = t.mode === 'debug' ? `Critically challenge this debug diagnosis + fix [plan] for the task.` : `Critically challenge this implementation [plan] for the task.`
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

async function runNaive(t) {
  const p = `You are a no-harness baseline implementer (Claude Sonnet 4.6). Solve this single task directly in ONE pass — no multi-agent process, no plan document, no separate review step. Just read the spec and write the correct solution.
${ISO(t)}
${WRITE('naive', t)}`
  const r = await agent(p, { label: `naive:${t.id}`, phase: 'naive', model: MODEL, schema: MANIFEST_SCHEMA })
  return { arm: 'naive', cat: t.cat, id: t.id, files: (r && r.files) || [], notes: (r && r.notes) || '' }
}

async function runArm(arm, t) {
  const plan = await agent(plannerP(arm, t), { label: `${arm}:plan:${t.id}`, phase: arm, model: MODEL })
  const [devil, research] = await parallel([
    () => agent(devilP(arm, t, plan), { label: `${arm}:devil:${t.id}`, phase: arm, model: MODEL }),
    () => agent(researchP(arm, t, plan), { label: `${arm}:research:${t.id}`, phase: arm, model: MODEL }),
  ])
  const r = await agent(implP(arm, t, plan, devil, research), { label: `${arm}:impl:${t.id}`, phase: arm, model: MODEL, schema: MANIFEST_SCHEMA })
  return { arm, cat: t.cat, id: t.id, files: (r && r.files) || [], notes: (r && r.notes) || '' }
}

const RUN = (arm, t) => (arm === 'naive' ? runNaive(t) : runArm(arm, t))

if (!JOBS.length) {
  log('NO JOBS provided via args.jobs — nothing to do (safe no-op). Pass args:{jobs:[{arm,cat,id,mode}]}.')
  return { ran: 0, note: 'no jobs' }
}
log(`Batch: ${JOBS.length} jobs -> ${JOBS.map((j) => `${j.arm}:${j.id}`).join(', ')}`)
const results = (await parallel(
  JOBS.map((j) => () =>
    RUN(j.arm, { cat: j.cat, id: j.id, mode: j.mode }).catch((e) => ({ arm: j.arm, cat: j.cat, id: j.id, files: [], error: String((e && e.message) || e) }))
  )
)).filter(Boolean)
const produced = results.filter((r) => !r.error && r.files && r.files.length).length
log(`Batch done: ${produced}/${results.length} jobs produced >=1 file.`)
return { ran: results.length, produced, results }
