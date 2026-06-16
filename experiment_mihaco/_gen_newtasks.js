export const meta = {
  name: 'mihaco-harness-gen',
  description: 'Generate MiHaCoBench candidate solutions per harness arm (naive/fast/general) with Sonnet 4.6 subagents that WRITE files directly to candidate dirs and return a small manifest',
  phases: [
    { title: 'naive', detail: '1 implementer/task, no harness', model: 'claude-sonnet-4-6' },
    { title: 'fast', detail: 'devil || research -> implementer (3/task)', model: 'claude-sonnet-4-6' },
    { title: 'general', detail: '3 analysts -> senior -> devil || research -> implementer -> QA(+revise) (8/task)', model: 'claude-sonnet-4-6' },
  ],
}

// Self-contained config (workflow `args` wiring is unreliable in this harness —
// see experiment_mihaco/RUNBOOK.md — so everything is embedded with `args` as an
// optional override). TO RUN THE GENERAL ARM LATER: set DEFAULT_ARMS = ['general']
// (or pass args.arms = ['general']) and re-invoke; pilot + naive/fast dirs are untouched.
const _A = (typeof args !== 'undefined' && args) ? args : {}
const DEFAULT_ARMS = ['naive', 'fast']
const BENCH = _A.bench_root || '/Users/hangyu/Desktop/MiHaCoBench'
const EXP = _A.exp_root || '/Users/hangyu/Desktop/MiHaCoBench/experiment_mihaco'
const ARMS = (_A.arms && _A.arms.length) ? _A.arms : DEFAULT_ARMS
const TASKS = (_A.tasks && _A.tasks.length) ? _A.tasks : [
  // The 2026-06-16 hard expansion (14 tasks) — validation run: naive vs fast.
  { cat: 'swe_bench', id: 'swe05_ledger_balance' },
  { cat: 'swe_bench', id: 'swe06_lru_writeback' },
  { cat: 'swe_bench', id: 'swe07_router_dispatch' },
  { cat: 'swe_bench', id: 'swe08_money_rounding' },
  { cat: 'complex', id: 'c07_migration_runner' },
  { cat: 'complex', id: 'c08_pivot_report' },
  { cat: 'easy', id: 'e06_semver_order' },
  { cat: 'compositional', id: 'cb05_config_validator' },
  { cat: 'compositional', id: 'cb06_timeseries_resample' },
  { cat: 'compositional', id: 'cb07_graph_spectral' },
  { cat: 'data_analysis', id: 'd07_paired_design' },
  { cat: 'data_analysis', id: 'd08_multiple_comparisons' },
  { cat: 'long_horizon', id: 'lh11_index_build' },
  { cat: 'long_horizon', id: 'lh12_budget_forecast' },
]
const MODEL = 'sonnet' // every generation subagent is held at Sonnet 4.6

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
- Create the EXACT filename(s) required by the spec's contract / "File layout" section (e.g. solution.py, or for multi-file tasks every named module). Flat layout unless the spec says otherwise.
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
    notes: { type: 'string', description: 'one line: approach or any spec ambiguity you resolved' },
  },
  required: ['files'],
  additionalProperties: true,
}
const QA_SCHEMA = {
  type: 'object',
  properties: {
    blocking: { type: 'boolean', description: 'true ONLY if a correctness-blocking defect must be fixed' },
    issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['blocking'],
  additionalProperties: true,
}

// ----------------------------- naive ----------------------------- //
async function runNaive(t) {
  const p = `You are a no-harness baseline implementer (Claude Sonnet 4.6). Solve this single coding task directly in one pass — no multi-agent process, no plan documents.
${ISO(t)}
${WRITE('naive', t)}`
  const r = await agent(p, { label: `naive:${t.id}`, phase: 'naive', model: MODEL, schema: MANIFEST_SCHEMA })
  return { arm: 'naive', cat: t.cat, id: t.id, subagents: 1, qa_blocking: null, files: (r && r.files) || [], files_inline: (r && r.files_inline) || [], notes: (r && r.notes) || '' }
}

// ----------------------------- fast ----------------------------- //
async function runFast(t) {
  const devilP = `You are the fast-harness Devil's Advocate (Sonnet 4.6). Anticipate how a naive implementation of THIS task would fail: edge cases, the exact complexity/memory gates, off-by-one and contract ambiguities, library-API misuse, determinism/plot/IO pitfalls.
${ISO(t)}
Return a concise bullet list (<=300 words) of concrete pitfalls to avoid. Do NOT write any files.`
  const researchP = `You determine the best-practice patterns needed to implement THIS task (fast-harness researcher, Sonnet 4.6). Name the correct current library APIs / algorithms / idioms required (exact signatures, the right data structure for any complexity gate, correct framework usage).
${ISO(t)}
Return a concise bullet list (<=300 words). Do NOT write any files.`
  const [devil, research] = await parallel([
    () => agent(devilP, { label: `fast:devil:${t.id}`, phase: 'fast', model: MODEL }),
    () => agent(researchP, { label: `fast:research:${t.id}`, phase: 'fast', model: MODEL }),
  ])
  const implP = `You are the fast-harness implementer (Sonnet 4.6). Implement and WRITE the solution for this task.
${ISO(t)}
Pitfalls to avoid (fast-harness Devil's Advocate):
${devil || '(none)'}
Best-practice patterns (fast-harness researcher):
${research || '(none)'}
${WRITE('fast', t)}`
  const r = await agent(implP, { label: `fast:impl:${t.id}`, phase: 'fast', model: MODEL, schema: MANIFEST_SCHEMA })
  return { arm: 'fast', cat: t.cat, id: t.id, subagents: 3, qa_blocking: null, files: (r && r.files) || [], files_inline: (r && r.files_inline) || [], notes: (r && r.notes) || '' }
}

// ----------------------------- general ----------------------------- //
async function runGeneral(t) {
  const fp = `Focus Analyst (Sonnet 4.6): reason depth-first on the key contract of THIS task.
${ISO(t)}
Return [plan 1] (<=350 words): approach, required entrypoints/files, the single hardest correctness/complexity risk and how to satisfy it. No files.`
  const bp = `Broad Analyst (Sonnet 4.6): enumerate EVERY requirement in the contract (all functions, all edge cases, all output artifacts).
${ISO(t)}
Return [plan 2] (<=350 words): a complete requirement checklist + an implementation outline. No files.`
  const frp = `Free Analyst (Sonnet 4.6): use your own judgment on how to approach THIS task.
${ISO(t)}
Return [plan 3] (<=350 words): recommended implementation strategy + any spec ambiguity and how you'd resolve it. No files.`
  const [focus, broad, free] = await parallel([
    () => agent(fp, { label: `gen:focus:${t.id}`, phase: 'general', model: MODEL }),
    () => agent(bp, { label: `gen:broad:${t.id}`, phase: 'general', model: MODEL }),
    () => agent(frp, { label: `gen:free:${t.id}`, phase: 'general', model: MODEL }),
  ])
  const sp = `Senior Engineer. Three analysts gave plans for this task; synthesize the single best implementation plan.
${ISO(t)}
[plan 1 - Focus]: ${focus || '-'}
[plan 2 - Broad]: ${broad || '-'}
[plan 3 - Free]: ${free || '-'}
Return [final plan] (<=400 words): the authoritative plan (files, entrypoints, exact algorithms for any complexity gate, edge cases, determinism). No files.`
  const senior = await agent(sp, { label: `gen:senior:${t.id}`, phase: 'general', model: MODEL })
  const gdP = `Critically challenge the [final plan] for this task (general-harness Devil's Advocate, Sonnet 4.6).
${ISO(t)}
[final plan]: ${senior || '-'}
Find concrete flaws: wrong/missing entrypoint, complexity-gate violation, contract mismatch, nondeterminism, IO/plot errors. Return <=250 words of must-fix items. No files.`
  const grP = `Verify the correct current library APIs and patterns needed for this task (general-harness researcher, Sonnet 4.6).
${ISO(t)}
[final plan]: ${senior || '-'}
Confirm exact signatures/idioms (scipy/sklearn/sqlalchemy/matplotlib/networkx/jinja2/etc. as relevant) and the right algorithm/data-structure for any gate. Return <=250 words. No files.`
  const [devil, research] = await parallel([
    () => agent(gdP, { label: `gen:devil:${t.id}`, phase: 'general', model: MODEL }),
    () => agent(grP, { label: `gen:research:${t.id}`, phase: 'general', model: MODEL }),
  ])
  const implP = `You are the general-harness implementer (Sonnet 4.6). Implement and WRITE the solution following the synthesized plan and the review.
${ISO(t)}
[final plan]: ${senior || '-'}
[must-fix criticisms]: ${devil || '-'}
[verified APIs/patterns]: ${research || '-'}
${WRITE('general', t)}`
  const impl = await agent(implP, { label: `gen:impl:${t.id}`, phase: 'general', model: MODEL, schema: MANIFEST_SCHEMA })
  const qaP = `QA Engineer (Sonnet 4.6). Review the just-written solution for this task against its spec. Read the spec ${specPath(t)} and the solution file(s) under ${targetDir('general', t)}. Check: required entrypoints present with correct signatures, contract satisfied, complexity/memory gate respected, determinism, required plots/IO produced.
${ISO(t)}
Return blocking=true ONLY for a correctness-blocking defect, plus the specific issues. Do NOT modify files.`
  const qa = await agent(qaP, { label: `gen:qa:${t.id}`, phase: 'general', model: MODEL, schema: QA_SCHEMA })
  const blocking = !!(qa && qa.blocking)
  if (blocking) {
    const revP = `You are the general-harness implementer (revision) (Sonnet 4.6). QA found blocking defect(s); fix them and RE-WRITE the corrected file(s) to the same directory.
${ISO(t)}
[QA blocking issues]: ${(qa && qa.issues && qa.issues.join('; ')) || 'see QA review'}
${WRITE('general', t)}`
    const rev = await agent(revP, { label: `gen:revise:${t.id}`, phase: 'general', model: MODEL, schema: MANIFEST_SCHEMA })
    return { arm: 'general', cat: t.cat, id: t.id, subagents: 8, qa_blocking: true, files: (rev && rev.files) || (impl && impl.files) || [], files_inline: (rev && rev.files_inline) || (impl && impl.files_inline) || [], notes: 'revised after QA' }
  }
  return { arm: 'general', cat: t.cat, id: t.id, subagents: 7, qa_blocking: false, files: (impl && impl.files) || [], files_inline: (impl && impl.files_inline) || [], notes: '' }
}

const RUN = { naive: runNaive, fast: runFast, general: runGeneral }

const jobs = []
for (const arm of ARMS) for (const t of TASKS) jobs.push({ arm, t })
log(`Generating ${jobs.length} arm-task solutions: arms=[${ARMS.join(',')}], tasks=${TASKS.length} (Sonnet 4.6 subagents)`)

const results = (await parallel(
  jobs.map((j) => () =>
    RUN[j.arm](j.t).catch((e) => ({ arm: j.arm, cat: j.t.cat, id: j.t.id, subagents: 0, files: [], files_inline: [], error: String((e && e.message) || e) }))
  )
)).filter(Boolean)

const produced = results.filter((r) => !r.error && ((r.files && r.files.length) || (r.files_inline && r.files_inline.length))).length
log(`Done: ${produced}/${results.length} arm-tasks produced >=1 file.`)
return { arms: ARMS, tasks: TASKS.length, results }
