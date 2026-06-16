export const meta = {
  name: 'author-tier2-hard-tasks',
  description: 'Author 7 tier-2 tasks designed to FAIL single-shot: complexity gates + a large system + c01-style ambiguity',
  phases: [
    { title: 'Author', detail: 'one agent per task: write TASK.md/manifest/grader/gold/broken, self-verify' },
    { title: 'Repair', detail: 'fix any task whose grader is not valid (gold all-pass AND broken >=1-fail)' },
  ],
}

const REPO = '/Users/hangyu/Desktop/MiHaCoBench'

const PREAMBLE = [
  'You are authoring ONE new benchmark task for MiHaCoBench (aka HarnessFlow PyBench).',
  'The repo root is ' + REPO + '. The Python interpreter is python3 (Python 3.11.5). There is no "python" on PATH.',
  '',
  'GOAL OF THIS BATCH (tier-2): unlike the fully-specified medium tasks, these are deliberately built so a strong model',
  'is likely to get them WRONG in one shot — EITHER because a wrong/naive algorithm physically times out on a hard',
  'feasibility gate, OR because a subtle boundary/ordering clause is easy to misread. Author them so the GOLD is correct',
  'and the difficulty is real (not a typo). Keep the contract precise, but let the difficulty live in the algorithm/edge cases.',
  '',
  'STEP 0 — read these first (in full):',
  '  - ' + REPO + '/_lib/AUTHORING_GUIDE.md  (authoring contract)',
  '  - ' + REPO + '/RUBRIC.md  sections 3, 4 (category methodology) and 5 (robustness)',
  '  - ' + REPO + '/_lib/grading_utils.py    (grader API: require_solution_dir, load_callable, load_module, run_cli, close,',
  '       run_within, time_limit, measure_runtime, estimate_time_complexity, within_one_tier, source_uses, code_quality_report)',
  '  - the EXEMPLAR task named in your brief — read its TASK.md, task.json, grader, gold AND __broken end to end and mirror its shape.',
  '',
  'HARD RULES (non-negotiable):',
  '  1. Grader integrity: the grader MUST pass EVERY test on the gold reference, and MUST fail at least one test on the broken reference.',
  '     The broken reference MUST still import and run cleanly (a logic/complexity defect that fails specific tests) — never crash at import.',
  '  2. Test the PUBLIC CONTRACT only. Floats via gu.close, never ==. Assert exception TYPES via pytest.raises, never messages.',
  '  3. Determinism: fixed, documented seeds for any random input; build large adversarial inputs with random.Random(seed) or numpy default_rng(seed).',
  '  4. Use ONLY packages in requirements.txt: numpy, pandas, scipy, scikit-learn (sklearn), matplotlib, pillow (PIL), SQLAlchemy,',
  '     jinja2, networkx, pyyaml (yaml), joblib, pytest, plus the Python stdlib. No new dependencies.',
  '  5. Add an advisory @pytest.mark.code_quality test that prints gu.code_quality_report(SOL) and never asserts.',
  '  6. The grader resolves code-under-test via gu.require_solution_dir(CATEGORY, TASK_ID) + gu.load_callable/load_module — NEVER hard-code a path.',
  '  7. TASK.md states the EXACT contract (signatures, return shapes, raised exception types, CLI, and for gated tasks the EXACT N + timeout).',
  '     Begin TASK.md with a header line: created date 2026-06-16, Category, Weight (mirror the exemplar header).',
  '',
  'COMPLEXITY-GATE TASKS (competitive/algorithmic): the grader MUST include a HARD feasibility gate — one large adversarial input',
  '  (fixed seed) wrapped in gu.run_within(TIMEOUT, fn, ...). Tune N + TIMEOUT during self-verify so that: the GOLD finishes with',
  '  >= 3x headroom under the timeout, and a naive/wrong-complexity approach would need >= 10x the timeout. Also add >= 8 (algorithmic)',
  '  or >= 10 (competitive) correctness tests incl. empty/singleton/boundary + an ADVERSARIAL input that defeats the tempting-but-wrong',
  '  approach, validated against an INDEPENDENT brute-force reference computed inside the grader on SMALL inputs. Add a soft_complexity test.',
  '',
  'ISOLATION — create/modify files ONLY under these two dirs for YOUR task:',
  '  - ' + REPO + '/tasks/<CATEGORY>/<TASK_ID>/   (TASK.md, task.json, grader/test_<SHORT>.py, data/ + expected/ only if needed)',
  '  - ' + REPO + '/_solutions/<CATEGORY>/<TASK_ID>/ (GOLD) and ' + REPO + '/_solutions/<CATEGORY>/<TASK_ID>__broken/ (BROKEN).',
  '  Do NOT touch README.md, RUBRIC.md, run_benchmark.py, _lib/, conftest.py, or any OTHER task/solution directory.',
  '',
  'task.json (write as ONE complete valid JSON file): { "id", "category", "title", "weight" (from brief), "packages": [...],',
  '  "entrypoints": {"module", "callables": [...], "cli": <bool>}, "grader": "grader/test_<SHORT>.py", "steps": null,',
  '  "complexity_target": "<e.g. O(n log n) or null>", "created": "2026-06-16" }',
  '',
].join('\n')

function VERIFY(s) {
  const grader = 'tasks/' + s.cat + '/' + s.id + '/grader/test_' + s.short + '.py'
  return [
    '',
    'SELF-VERIFY (run from the repo root ' + REPO + ', iterate until BOTH hold):',
    '  Gold must FULLY pass:  cd ' + REPO + ' && MPLBACKEND=Agg PYTHONHASHSEED=0 python3 -m pytest ' + grader + ' -p no:cacheprovider -q',
    '  Broken must fail >=1:  cd ' + REPO + ' && MPLBACKEND=Agg PYTHONHASHSEED=0 PYBENCH_VARIANT=broken python3 -m pytest ' + grader + ' -p no:cacheprovider -q',
    'For a gated task, ALSO time the gold on the large input (print the seconds) and confirm it is comfortably under the timeout with >=3x headroom;',
    'if it is borderline, lower N or raise the timeout, and ensure a naive approach would still blow the gate by >=10x.',
    'Do not weaken a test to make it pass — keep the difficulty real. Do not finish until both conditions hold.',
    'Return ONLY the structured result; set ok=true ONLY if you personally observed gold fully green AND broken with >=1 failure this session.',
    'Put the verbatim pytest summary lines into gold_summary and broken_summary.',
  ].join('\n')
}

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['id', 'ok', 'gold_summary', 'broken_summary', 'files', 'notes'],
  properties: {
    id: { type: 'string' },
    ok: { type: 'boolean' },
    gold_summary: { type: 'string' },
    broken_summary: { type: 'string' },
    gold_gate_seconds: { type: 'string', description: 'for gated tasks: measured gold seconds on the large input + the timeout' },
    files: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string', description: 'the planted defect / the subtle clause, the gate N+timeout, and anything to double-check' },
  },
}

const SPECS = [
  // ---------------- complexity-gated hard algorithmic ----------------
  {
    id: 'cp05_kth_subarray_sum', cat: 'competitive', short: 'cp05', weight: 8, module: 'solution.py', cli: false,
    packages: ['stdlib'], exemplar: 'competitive/cp04_tree_distance',
    brief: [
      'TITLE: k-th smallest contiguous-subarray sum of a non-negative array (binary-search-on-answer + sliding window).',
      'Single file solution.py, stdlib only.',
      'Contract: kth_subarray_sum(a: list[int], k: int) -> int. a has n>=1 non-negative ints. Among ALL n*(n+1)/2 contiguous',
      '  subarray sums (each contiguous subarray a[i..j], i<=j), return the k-th SMALLEST (1-indexed; k between 1 and n*(n+1)/2).',
      'GOLD algorithm (REQUIRED to pass the gate): binary search the answer S over [min element, total sum]; count subarrays with',
      '  sum <= S using a two-pointer sliding window (valid because all elements are non-negative, so window sums are monotonic);',
      '  return the smallest S with count >= k. Overall O(n log(totalSum)). n<=1 handled.',
      'INDEPENDENT reference in the grader (small n only): brute force all subarray sums, sort, pick the k-th.',
      'HARD GATE: build a fixed-seed (random.Random(SEED)) non-negative array of length N (tune N around 1.2e5 with values 0..1000)',
      '  and a k near the middle; run kth_subarray_sum under gu.run_within(TIMEOUT) with TIMEOUT tuned so gold has >=3x headroom',
      '  (target ~6-10s). A naive O(n^2) enumeration of ~7e9 subarray sums blows this by far. State the exact N + TIMEOUT in TASK.md.',
      'BROKEN (planted defect): the O(n^2) brute force (enumerate-and-sort). It is CORRECT but blows the hard gate (times out) — so the',
      '  gate test fails on broken while every small correctness test still passes. (Alternatively an off-by-one in the count predicate;',
      '  pick the O(n^2) brute force so the discriminator is unambiguously the complexity gate.)',
      'GRADER test_cp05.py (>=10 tests): singleton; all-equal; k=1 (the minimum element); k=max (the total sum); a known small case',
      '  checked against the brute reference; several random small cases vs brute; the HARD GATE (gu.run_within) as the complexity',
      '  discriminator; a soft_complexity test (advisory, within_one_tier of O(n log n) allowing O(n^2)); the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'cp06_range_distinct_offline', cat: 'competitive', short: 'cp06', weight: 8, module: 'solution.py', cli: false,
    packages: ['stdlib'], exemplar: 'competitive/cp04_tree_distance',
    brief: [
      'TITLE: Offline range "number of distinct values in a[l..r]" queries via a Fenwick/BIT (last-occurrence trick).',
      'Single file solution.py, stdlib only.',
      'Contract: range_distinct(a: list[int], queries: list[tuple]) -> list[int]. a has n values (any hashable ints). queries is a list',
      '  of (l, r) 0-indexed INCLUSIVE ranges (0 <= l <= r < n). Return, per query, the count of DISTINCT values in a[l..r], in the',
      '  SAME order as the input queries.',
      'GOLD algorithm (REQUIRED to pass the gate): OFFLINE. Sort query indices by r ascending. Sweep i = 0..n-1 maintaining a Fenwick',
      '  tree over positions: when reaching position i with value v, if v was last seen at position p>=0 do bit.add(p, -1); bit.add(i, +1);',
      '  record last[v] = i. Answer every query with r == i as bit.range_sum(l, i). Overall O((n+q) log n). Restore input order at the end.',
      'INDEPENDENT reference in the grader (small n only): for each query compute len(set(a[l:r+1])).',
      'HARD GATE: build a fixed-seed array of length N (~1e5, values drawn from a modest alphabet so distinctness varies) and Q (~1e5)',
      '  random valid (l,r) queries; run range_distinct under gu.run_within(TIMEOUT) tuned for >=3x gold headroom (~6-10s). A naive',
      '  O(n) per query (len(set(...))) is O(n*q) ~ 1e10 and blows the gate. State exact N, Q, TIMEOUT in TASK.md.',
      'BROKEN (planted defect): the naive per-query len(set(a[l:r+1])) implementation. CORRECT but O(n*q) — blows the hard gate while',
      '  all small correctness tests still pass.',
      'GRADER test_cp06.py (>=10 tests): single element; whole-array query; many singleton-range queries; all-distinct array; all-equal',
      '  array; order-preservation of results vs input query order; several random small cases vs the set() reference; the HARD GATE;',
      '  a soft_complexity test (advisory); the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'a08_cooldown_profit', cat: 'algorithmic', short: 'a08', weight: 8, module: 'solution.py', cli: false,
    packages: ['stdlib'], exemplar: 'algorithmic/a04_edit_distance',
    brief: [
      'TITLE: Maximum-profit non-overlapping weighted intervals with a mandatory cooldown gap (weighted interval scheduling, twisted).',
      'Single file solution.py, stdlib only. This is the HARD algorithmic tier (weight 8).',
      'Contract: max_profit(jobs: list[tuple], gap: int) -> int. Each job is (start, end, profit) with integer start < end and profit >= 0.',
      '  Select a subset of NON-OVERLAPPING jobs such that, for any two chosen jobs, the next job\'s start is >= the previous chosen',
      '  job\'s end PLUS gap (a required cooldown of at least `gap` between consecutive selected jobs). Maximize total profit. Return the',
      '  max total profit (0 if jobs is empty). Jobs are half-open [start, end): two jobs with prevEnd + gap <= nextStart may both be chosen.',
      'GOLD algorithm (REQUIRED to pass the gate): sort jobs by end; dp[i] = best profit using the first i jobs (sorted). For job i with',
      '  (s,e,p): dp[i] = max(dp[i-1], p + best dp over jobs whose end <= s - gap) via binary search on the sorted ends + a running prefix',
      '  max. Overall O(n log n). Return dp[n].',
      'WHY IT IS HARD: a greedy that picks highest-profit-first, or earliest-end-first without the DP, is WRONG. A naive O(n^2) DP is correct',
      '  but blows the gate.',
      'INDEPENDENT reference in the grader (small n only): an O(n^2) DP (or exhaustive subset search for very small n).',
      'HARD GATE: build a fixed-seed set of N jobs (~2e5) with random starts/durations/profits and a fixed gap; run max_profit under',
      '  gu.run_within(TIMEOUT) tuned for >=3x gold headroom (~5-8s). A naive O(n^2) DP (~4e10) blows it. State exact N + TIMEOUT in TASK.md.',
      'BROKEN (planted defect): a greedy that sorts by profit descending and picks any job compatible with the cooldown — produces a',
      '  SUBOPTIMAL total on a constructed adversarial case (gold passes, greedy fails). The broken still runs fast (so the discriminator',
      '  is the adversarial CORRECTNESS test, not the gate). Include that adversarial case explicitly in the grader.',
      'GRADER test_a08.py (>=8 tests): empty -> 0; single job -> its profit; two overlapping jobs -> the better one; two jobs separated',
      '  by exactly gap (both selectable) vs gap-1 (only one); the ADVERSARIAL greedy-defeating case (a cluster of small-profit jobs that',
      '  beats one big-profit job); several random small cases vs the O(n^2) reference; the HARD GATE; a soft_complexity test; advisory code_quality.',
    ].join('\n'),
  },

  // ---------------- large intricate system ----------------
  {
    id: 'c09_reactive_engine', cat: 'complex', short: 'c09', weight: 5, module: 'engine.py', cli: false,
    packages: ['networkx'], exemplar: 'complex/c03_graph_engine',
    brief: [
      'TITLE: Reactive dataflow engine — transitive cache invalidation + topological batch recompute + cycle detection.',
      'STYLE: large intricate multi-module system; many interacting constraints make one-shot correctness unlikely. Use networkx for the',
      '  dependency graph. Read c03_graph_engine (networkx idioms) and c04_formula_engine first. Multi-file: e.g. graph.py (dependency',
      '  tracking) and engine.py (the FACADE).',
      'Public contract (importable from engine.py):',
      '  class Engine:',
      '    set_value(name, value): define/replace a constant cell holding `value`. Replacing a cell INVALIDATES the cached value of the',
      '      cell and ALL its transitive dependents (so their next get() recomputes).',
      '    set_formula(name, deps: list[str], fn): define/replace a computed cell whose value is fn(*[get(d) for d in deps]); registers',
      '      edges deps -> name in the dependency graph. Replacing a formula re-points its dependencies and invalidates transitive dependents.',
      '      Introducing a cycle MUST raise ValueError (detected via networkx, e.g. a back edge / not a DAG) and leave the engine unchanged.',
      '    get(name) -> value: return the cell value, recomputing lazily from dependencies if its cache is invalid, and MEMOIZING the result;',
      '      a clean cache is returned without recomputation. Unknown name -> KeyError.',
      '    recompute_count(name) -> int: how many times `name` has actually been (re)computed since creation (to prove memoization +',
      '      single-recompute-per-invalidation; a get() on a clean cache does NOT increment it).',
      '    batch(updates: dict): apply several set_value updates atomically, then ensure each affected cell recomputes AT MOST ONCE on the',
      '      next reads (i.e. invalidation is set-based, not per-edge). Order of recomputation must respect topological order of dependencies.',
      'GOLD: set_value/set_formula invalidate the dirtied cell AND all transitive dependents (use networkx.descendants); get() recomputes',
      '  only when dirty, memoizes, and increments recompute_count exactly once per recomputation; cycles raise ValueError and roll back.',
      'BROKEN (planted defect): invalidation does NOT propagate transitively — set_value(name, v) marks only `name` dirty, leaving',
      '  dependents with stale cached values. So after updating an input, a downstream formula get() returns the OLD result. (Direct',
      '  dependents that were never yet computed still compute correctly, so basic tests pass; the transitive-stale test fails.)',
      'GRADER test_c09.py (>=10 small per-behavior tests for partial credit): constant get; simple formula over two constants; chained',
      '  formula a->b->c; TRANSITIVE invalidation (update a leaf, read a 2-hops-away dependent, get the NEW value) [FAIL_TO_PASS];',
      '  memoization (two get()s -> recompute_count increments once); single-recompute-per-invalidation; unknown name KeyError; direct',
      '  cycle and indirect cycle raise ValueError and leave the engine usable; a batch update recomputes each affected cell once.',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },

  // ---------------- c01-style subtle ambiguity ----------------
  {
    id: 'dbg07_token_bucket', cat: 'debug', short: 'dbg07', weight: 2, module: 'solution.py', cli: false,
    packages: ['stdlib'], exemplar: 'debug/dbg01_retry_runner',
    brief: [
      'TITLE: Token-bucket rate limiter with a SUBTLE boundary defect (refill timing + inclusive admission).',
      'STYLE: debug (SWE-bench FAIL_TO_PASS / PASS_TO_PASS). The broken reference IS the still-buggy code; the planted defect is a',
      '  c01-style boundary off-by-one that careful vs hasty implementations resolve differently. Single file solution.py, stdlib only.',
      'TASK.md embeds the buggy implementation and a behavioural repro (the exact boundary case), and asks for a corrected solution.py.',
      'Public contract:',
      '  class TokenBucket(capacity: int, refill_rate: float): a bucket holding up to `capacity` tokens, refilling `refill_rate` tokens',
      '    per second, starting FULL at time 0. allow(now: float) -> bool: FIRST refill the bucket based on elapsed time since the last',
      '    call (tokens = min(capacity, tokens + elapsed*refill_rate)), capped at capacity; THEN if tokens >= 1.0 consume exactly one token',
      '    and return True (request admitted), else return False. `now` is non-decreasing across calls.',
      'CORRECT (gold) boundary semantics, stated precisely in TASK.md: refill-THEN-admit; admission requires tokens >= 1.0 (inclusive); a',
      '  request that brings tokens to exactly 1.0 via refill IS admitted; tokens never exceed capacity.',
      'BROKEN/buggy reference (the defect to fix): it admits BEFORE refilling (checks the stale token count, then refills) AND uses a',
      '  strict tokens > 1.0 test, so a request exactly at the moment the bucket refills the 1st token is WRONGLY denied. Basic burst/deny',
      '  behaviour away from the boundary still works (PASS_TO_PASS).',
      'GRADER test_dbg07.py (>=6 tests): initial burst of `capacity` immediate allows then a deny (P2P); long wait refills to full and',
      '  caps at capacity (P2P); FAIL_TO_PASS: a request at exactly the refill boundary (e.g. capacity=1, refill_rate=1, allow(0)->True',
      '  consumes the token, allow(1.0)->True because exactly one token refilled) — buggy denies, gold admits; partial-second refill does',
      '  NOT over-credit; admission is inclusive at the 1.0 boundary. Use gu.close for token timing where needed; never assert messages.',
      '  Add the advisory code_quality test. Keep the planted bug localized so the broken ref passes every P2P and fails >=1 F2P.',
    ].join('\n'),
  },
  {
    id: 'cb08_cursor_paginate', cat: 'compositional', short: 'cb08', weight: 4, module: 'solution.py', cli: false,
    packages: ['pandas'], exemplar: 'compositional/cb01_log_analytics',
    brief: [
      'TITLE: Stable cursor pagination over a sorted DataFrame — EXCLUSIVE cursor + tie-break ambiguity. Composes pandas + json + base64.',
      'STYLE: compositional (>=2 libs) with a c01-style subtle ordering clause. Single file solution.py.',
      'Public contract:',
      '  paginate(df: pandas.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict. Rows are ordered by',
      '    (df[sort_key] ASC, df["id"] ASC) — `id` is the stable tie-breaker (assume an integer "id" column, unique). A page returns the',
      '    first `page_size` rows STRICTLY AFTER the cursor position in that order. cursor=None starts at the beginning. The cursor token is',
      '    an opaque base64(json) of the last returned row\'s (sort_key value, id). Return {"rows": list[dict] (the page rows as records),',
      '    "next_cursor": str | None (None when the page is the last; NO trailing empty page — if exactly page_size rows remain and they',
      '    are the final rows, next_cursor is None)}.',
      'PRECISE (and easy-to-misread) semantics, stated in TASK.md: the cursor is EXCLUSIVE — the row equal to the cursor is NOT repeated;',
      '  "strictly after" means (sort_key, id) lexicographically greater than the cursor\'s (sort_key, id); ties on sort_key are broken by id',
      '  ascending so pagination never skips or duplicates a tied row; there is NEVER a trailing empty page.',
      'EXCEPTION CONTRACT: a malformed/undecodable cursor -> ValueError; page_size < 1 -> ValueError; missing "id" or sort_key column -> KeyError.',
      'GOLD: exclusive cursor via the (sort_key, id) lexicographic comparison; correct last-page next_cursor=None; stable tie-break.',
      'BROKEN (planted defect): the cursor is treated as INCLUSIVE (uses >= on the boundary, or compares only sort_key ignoring id), so the',
      '  boundary row is DUPLICATED across consecutive pages (or tied rows get skipped/duplicated). Single-page and first-page cases still pass.',
      'GRADER test_cb08.py (>=8 tests): build a fixed DataFrame inline including a block of TIED sort_key values spanning a page boundary.',
      '  Tests: first page rows + next_cursor; full walk via repeated calls returns EVERY row exactly once in order with NO duplicates and',
      '  NO omissions [FAIL_TO_PASS — the inclusive-cursor bug duplicates the boundary row]; last page has next_cursor None and no trailing',
      '  empty page; tie block paginated correctly across the boundary; exception paths (bad cursor ValueError, page_size 0 ValueError,',
      '  missing column KeyError). Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'a09_interval_stab', cat: 'algorithmic', short: 'a09', weight: 4, module: 'solution.py', cli: false,
    packages: ['stdlib'], exemplar: 'algorithmic/a04_edit_distance',
    brief: [
      'TITLE: Minimum points to stab all CLOSED intervals — a touching-endpoint ambiguity (closed vs half-open). Medium algorithmic (weight 4).',
      'Single file solution.py, stdlib only.',
      'Contract: min_stabbing_points(intervals: list[tuple]) -> int. Each interval is (a, b) with a <= b, a CLOSED interval [a, b]. Return the',
      '  minimum number of points on the real line such that every interval contains at least one chosen point. A point p stabs [a,b] iff',
      '  a <= p <= b (INCLUSIVE at both ends). Empty list -> 0.',
      'PRECISE (and easy-to-misread) semantics, stated in TASK.md: intervals are CLOSED, so two intervals that merely TOUCH at an endpoint',
      '  (e.g. [1,2] and [2,3]) share the point 2 and can be stabbed by ONE point. (A half-open reading would need two — that is the trap.)',
      'GOLD algorithm: sort intervals by right endpoint ascending; greedily place a point at the right endpoint of the first not-yet-stabbed',
      '  interval; skip all subsequent intervals whose left endpoint <= that point (inclusive). O(n log n).',
      'BROKEN (planted defect): uses a STRICT comparison at the boundary (treats intervals as half-open) — when deciding whether the current',
      '  point stabs the next interval it uses point < a or a > point with strict inequality at the touching endpoint, so touching intervals',
      '  are counted as needing a separate point. Non-touching cases still pass.',
      'GRADER test_a09.py (>=8 tests): empty -> 0; single interval -> 1; fully nested intervals -> 1; disjoint intervals -> their count;',
      '  the TOUCHING case [1,2],[2,3] -> 1 [FAIL_TO_PASS]; a chain of touching intervals [0,1],[1,2],[2,3],[3,4] -> the correct small',
      '  count [FAIL_TO_PASS]; a larger mixed case vs an independent brute-force/greedy reference; a fixed-seed medium input for a light',
      '  O(n log n) sanity (not a hard gate — this is medium). Add the advisory code_quality test.',
    ].join('\n'),
  },
]

function briefText(s) {
  const ep = 'entrypoints module = "' + s.module + '", cli = ' + (s.cli ? 'true' : 'false') + ', steps = null'
  return [
    '================ YOUR TASK ================',
    'TASK_ID = ' + s.id + '   CATEGORY = ' + s.cat + '   WEIGHT = ' + s.weight,
    'grader file = grader/test_' + s.short + '.py   ' + ep + '   packages = ' + JSON.stringify(s.packages),
    'EXEMPLAR to read and mirror: tasks/' + s.exemplar + '/ and _solutions/' + s.exemplar + '/ (+ its __broken).',
    '',
    s.brief,
  ].join('\n')
}

phase('Author')
const results = await pipeline(
  SPECS,
  (s) => agent(PREAMBLE + '\n' + briefText(s) + '\n' + VERIFY(s),
    { label: 'author:' + s.id, phase: 'Author', schema: SCHEMA }),
  (res, s) => {
    if (res && res.ok) return res
    const ctx = res
      ? ('A previous attempt reported NOT-valid. gold="' + (res.gold_summary || '?') + '" broken="' +
         (res.broken_summary || '?') + '" notes="' + (res.notes || '') + '". ')
      : 'A previous attempt failed to produce a usable result. '
    return agent(
      PREAMBLE + '\n' + briefText(s) + '\n' + VERIFY(s) +
      '\n\nREPAIR MODE: ' + ctx +
      'Re-read the files on disk for this task, run BOTH verification commands, diagnose, and fix whichever of {gold, grader, broken} ' +
      'is wrong (for a gated task, re-tune N/timeout so gold has >=3x headroom) until gold is fully green AND broken has >=1 failure. ' +
      'Then return the structured result from what you actually observed.',
      { label: 'repair:' + s.id, phase: 'Repair', schema: SCHEMA })
  },
)

const ok = results.filter((r) => r && r.ok)
const bad = results.filter((r) => !r || !r.ok)
log('Tier-2 authoring complete: ' + ok.length + '/' + SPECS.length + ' tasks self-checked valid.')
if (bad.length) log('NOT valid: ' + bad.map((r, i) => (r && r.id) || (SPECS[i] && SPECS[i].id)).join(', '))
return { valid: ok.map((r) => r.id), invalid: bad.map((r) => r && r.id), results }
