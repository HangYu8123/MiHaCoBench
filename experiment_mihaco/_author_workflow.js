export const meta = {
  name: 'author-hard-tasks',
  description: 'Author 14 new hard, harness-discriminating MiHaCoBench tasks (gold+broken+grader, self-checked)',
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
  'STEP 0 — read these first (in full), they define the exact contract you must mirror:',
  '  - ' + REPO + '/_lib/AUTHORING_GUIDE.md  (the authoring contract)',
  '  - ' + REPO + '/_lib/grading_utils.py    (the grader API: require_solution_dir, load_callable, load_module,',
  '       run_cli, close, png_is_valid, count_valid_pngs, source_uses, run_provenance_chain, sha256_file, code_quality_report)',
  '  - the EXEMPLAR task named in your brief below — read its TASK.md, task.json, grader, gold AND __broken solution end to end and mirror its shape exactly.',
  '',
  'HARD RULES (non-negotiable, from RUBRIC.md / AUTHORING_GUIDE.md):',
  '  1. Grader integrity: the grader MUST pass EVERY test on the gold reference, and MUST fail at least one test on the broken reference.',
  '     The broken reference MUST still import and run cleanly (a logic bug that fails specific tests) — it must NOT crash at import/collection.',
  '  2. Test the PUBLIC CONTRACT only — never internal names/structure/import order.',
  '  3. Floats compared via gu.close / tolerance, never ==. Assert exception TYPES (pytest.raises(T)), never messages.',
  '  4. Determinism: fixed seeds; commit any dataset under the task data/ dir; never generate random data inside the grader.',
  '  5. Use ONLY packages already in requirements.txt: numpy, pandas, scipy, scikit-learn, matplotlib, pillow (PIL),',
  '     SQLAlchemy, jinja2, networkx, pyyaml (yaml), joblib, pytest, plus the Python stdlib. Do NOT add new dependencies.',
  '  6. Add an advisory @pytest.mark.code_quality test that prints gu.code_quality_report(SOL) and never asserts pass/fail.',
  '  7. The grader resolves the code under test via gu.require_solution_dir(CATEGORY, TASK_ID) + gu.load_callable/load_module — NEVER hard-code a path.',
  '  8. TASK.md must state the EXACT output contract (file names, function signatures, dict keys, dtypes, raised exception types, CLI).',
  '     Begin TASK.md with a header line containing the created date 2026-06-16 and the Category + Weight, mirroring the exemplar.',
  '',
  'ISOLATION — you may create/modify files ONLY under these two directories for YOUR task:',
  '  - ' + REPO + '/tasks/<CATEGORY>/<TASK_ID>/        (TASK.md, task.json, grader/test_<SHORT>.py, and data/ + expected/ if your brief needs them)',
  '  - ' + REPO + '/_solutions/<CATEGORY>/<TASK_ID>/   (GOLD reference) and ' + REPO + '/_solutions/<CATEGORY>/<TASK_ID>__broken/ (BROKEN reference)',
  '  Do NOT touch README.md, RUBRIC.md, run_benchmark.py, _lib/, conftest.py, or any OTHER task/solution directory. Other agents are authoring sibling tasks concurrently.',
  '',
  'task.json shape (write it as ONE complete, valid JSON file in a single write — do not leave it half-written):',
  '  { "id": TASK_ID, "category": CATEGORY, "title": "...", "weight": <from brief>, "packages": [...],',
  '    "entrypoints": {"module": "<entry module>", "callables": [...], "cli": <bool>}, "grader": "grader/test_<SHORT>.py",',
  '    "steps": <int for long_horizon else null>, "complexity_target": null, "created": "2026-06-16" }',
  '',
].join('\n')

function VERIFY(s) {
  const grader = 'tasks/' + s.cat + '/' + s.id + '/grader/test_' + s.short + '.py'
  return [
    '',
    'SELF-VERIFY (run from the repo root ' + REPO + ', iterate until BOTH conditions hold):',
    '  Gold must FULLY pass:',
    '    cd ' + REPO + ' && MPLBACKEND=Agg PYTHONHASHSEED=0 python3 -m pytest ' + grader + ' -p no:cacheprovider -q',
    '    -> every test passes (0 failed, 0 errors). code_quality/soft markers run and pass (they never assert).',
    '  Broken must fail at least one test (and still import cleanly):',
    '    cd ' + REPO + ' && MPLBACKEND=Agg PYTHONHASHSEED=0 PYBENCH_VARIANT=broken python3 -m pytest ' + grader + ' -p no:cacheprovider -q',
    '    -> at least 1 test FAILS; collection must succeed (no import/collection error counting all tests as errored).',
    'If gold is not fully green, fix the GOLD or the GRADER. If broken passes everything, make the planted defect bite a test.',
    'Do not finish until both conditions hold. Do not weaken a test just to make it pass — keep the contract meaningful.',
    '',
    'When done, return ONLY the structured result (the StructuredOutput tool): set ok=true ONLY if you personally ran both',
    'commands above in this session and observed gold fully green AND broken with >=1 failure. Put the final pytest summary',
    'lines (e.g. "12 passed" / "1 failed, 11 passed") into gold_summary and broken_summary verbatim.',
  ].join('\n')
}

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['id', 'ok', 'gold_summary', 'broken_summary', 'files', 'notes'],
  properties: {
    id: { type: 'string' },
    ok: { type: 'boolean', description: 'true ONLY if gold fully passed AND broken had >=1 failure, both observed this session' },
    gold_summary: { type: 'string', description: 'verbatim pytest summary line for the GOLD run' },
    broken_summary: { type: 'string', description: 'verbatim pytest summary line for the BROKEN run' },
    files: { type: 'array', items: { type: 'string' }, description: 'repo-relative paths created' },
    notes: { type: 'string', description: 'the planted defect, any deviations, and anything the reviewer should check' },
  },
}

// ---------------------------------------------------------------------------
// The 14 task briefs. Each maps to one of the user-chosen discriminating styles:
//   SWE multi-file fault-localization | spec-density traps | multi-lib + state/stats.
// ---------------------------------------------------------------------------
const SPECS = [
  // ===================== SWE_BENCH (multi-file fault localization) =====================
  {
    id: 'swe05_ledger_balance', cat: 'swe_bench', short: 'swe05', weight: 6, module: 'ledger.py', cli: false,
    packages: [], exemplar: 'swe_bench/swe02_mini_orm',
    brief: [
      'TITLE: Double-entry ledger across 3 modules (sign bug crosses a module boundary).',
      'STYLE: SWE-bench multi-file fault localization. The SYMPTOM is observed in ledger.py but the ROOT CAUSE is in transactions.py.',
      'Stdlib only. Create THREE modules in both the gold and the broken solution dirs:',
      '  accounts.py  — class Account(name): integer-cent balance starting at 0; method apply(amount_cents: int) -> None that adds the signed amount to the balance.',
      '  transactions.py — function post_entries(entries, accounts) where entries is a list of (account_name, amount_cents) signed ints and accounts is a dict name->Account.',
      '       It applies EVERY entry: for each (name, amount) it calls accounts[name].apply(amount). (This is the file the bug lives in.)',
      '  ledger.py (FACADE) — class Ledger: add_account(name) creates an Account (duplicate name raises ValueError); post(entries): validate that sum of all entry amounts == 0 (else raise ValueError "entries must balance"),',
      '       and every referenced account exists (else KeyError), then delegate to transactions.post_entries; balance(name) -> int cents; trial_balance() -> int = sum of all account balances (must be 0 after any balanced posting).',
      'ledger.py must re-export so the grader can do: from ledger import Ledger.',
      'GOLD behaviour: post_entries applies all entries as-is, so a transfer entries=[("A",-100),("B",100)] gives balance("A")==-100, balance("B")==100, trial_balance()==0.',
      'BROKEN (the planted defect, in transactions.py ONLY): post_entries silently DROPS entries with a negative amount (e.g. `for name,amt in entries:` `if amt < 0: continue` then apply). So credits post but debits are ignored: balance("A")==0, balance("B")==100, trial_balance()==100. Validation in ledger.py still passes (it sums the original entries), so the bug is invisible until you inspect balances.',
      'GRADER test_swe05.py (>=8 tests). Mirror swe02. Include:',
      '  PASS_TO_PASS (true in gold AND broken): add_account works; duplicate account raises ValueError; unbalanced entries raise ValueError; posting to a missing account raises KeyError; a fresh account balance is 0; a single self-cancelling pair where BOTH amounts... no—keep PASS_TO_PASS ones that do not depend on debits posting.',
      '  FAIL_TO_PASS (true in gold, FALSE in broken): after a balanced transfer, the debited account balance is negative and trial_balance()==0; a multi-entry balanced posting leaves trial_balance()==0 and each balance correct.',
      '  Use exact integer equality for cents (no floats). Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'swe06_lru_writeback', cat: 'swe_bench', short: 'swe06', weight: 6, module: 'kv.py', cli: false,
    packages: [], exemplar: 'swe_bench/swe02_mini_orm',
    brief: [
      'TITLE: Write-through LRU cache over a backing store across 3 modules (stale-read bug crosses a module boundary).',
      'STYLE: SWE-bench multi-file fault localization. SYMPTOM observed via kv.get (kv.py); ROOT CAUSE in cache.py.',
      'Stdlib only. Three modules in gold and broken:',
      '  store.py — class Backing: dict-backed get(key) -> value (KeyError if absent) and set(key, value).',
      '  cache.py — class LRU(capacity): a hand-rolled LRU. MISS = a module-level sentinel object. get(key) returns value or MISS and marks the key most-recently-used; put(key, value) inserts/updates and marks MRU, evicting the least-recently-used when over capacity; invalidate(key) drops a key if present. (This file holds the bug.)',
      '  kv.py (FACADE) — class KV(backing, capacity): get(key): on cache hit return it; on miss read backing (KeyError if absent), populate the cache, return value. set(key, value): write-through — backing.set then cache.put(key, value).',
      'kv.py must allow: from kv import KV.',
      'GOLD: cache.put on an EXISTING key overwrites the stored value and marks it MRU. So: kv.set("k",1); kv.get("k")==1; kv.set("k",2); kv.get("k")==2.',
      'BROKEN (planted defect, in cache.py ONLY): LRU.put, when the key already exists, only updates recency and RETURNS EARLY without overwriting the stored value (e.g. `if key in self._data: self._touch(key); return`). New keys and eviction still work. Effect: after kv.set("k",2) the cache still serves the stale 1, so kv.get("k")==1.',
      'GRADER test_swe06.py (>=8 tests). Include:',
      '  PASS_TO_PASS (gold AND broken): basic set then get of a fresh key; get of a key only in the backing falls through and caches it; get of a truly absent key raises KeyError; eviction — with capacity 2, inserting 3 distinct keys evicts the LRU one (verify via backing fallback still returns it); MISS sentinel semantics if exposed.',
      '  FAIL_TO_PASS (gold true, broken false): updating an existing key via kv.set then kv.get returns the NEW value; repeated updates always reflect the latest write.',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'swe07_router_dispatch', cat: 'swe_bench', short: 'swe07', weight: 6, module: 'app.py', cli: false,
    packages: [], exemplar: 'swe_bench/swe02_mini_orm',
    brief: [
      'TITLE: Tiny path router with typed params across 3 modules (trailing-slash normalization bug crosses a module boundary).',
      'STYLE: SWE-bench multi-file fault localization. SYMPTOM observed via app.handle (app.py); ROOT CAUSE in path.py.',
      'Stdlib only. Three modules in gold and broken:',
      '  path.py — function split_path(p: str) -> list[str]: normalize a URL path into its non-empty segments. GOLD: `[seg for seg in p.strip("/").split("/") if seg]` so "/users/5", "/users/5/", and "users/5" all -> ["users","5"], and "/" and "" -> []. (This file holds the bug.)',
      '  router.py — class Router: add(pattern, handler_name) where pattern is like "/users/{id}/posts/{pid}"; match(path) -> (handler_name, params: dict) or None. A pattern matches iff split_path(pattern) and split_path(path) have EQUAL length and every literal segment matches; {name} segments capture the corresponding path segment as a string into params. Use path.split_path for BOTH sides.',
      '  app.py (FACADE) — class App: route(pattern, handler_name) delegates to Router.add; handle(path) -> dict {"handler": name, "params": {...}} for a match, or {"handler": None, "params": {}} for no match.',
      'app.py must allow: from app import App.',
      'GOLD: handle("/users/5/") matches route "/users/{id}" -> {"handler":"show","params":{"id":"5"}} because the trailing slash is stripped.',
      'BROKEN (planted defect, in path.py ONLY): split_path only strips the LEADING slash: `[seg for seg in p.lstrip("/").split("/") if seg or True]`... keep it realistic: GOLD strips both ends and drops empties; BROKEN uses `p.lstrip("/").split("/")` WITHOUT dropping empty segments, so "/users/5/" -> ["users","5",""] (length 3) and no longer matches the length-2 pattern -> handle returns {"handler": None,...}. Paths without a trailing slash still work.',
      'GRADER test_swe07.py (>=8 tests). Include:',
      '  PASS_TO_PASS (gold AND broken): a static route "/health" matches; a single-param route "/users/{id}" matches "/users/5" with id="5"; a two-param route extracts both; a non-matching path returns handler None; a path with the wrong segment count returns None.',
      '  FAIL_TO_PASS (gold true, broken false): handle("/users/5/") (trailing slash) matches and returns id="5"; the root path "/" routes to a registered root handler.',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'swe08_money_rounding', cat: 'swe_bench', short: 'swe08', weight: 6, module: 'invoice.py', cli: false,
    packages: [], exemplar: 'swe_bench/swe02_mini_orm',
    brief: [
      'TITLE: Invoice totals with per-line tax rounding across 3 modules (truncation-vs-round bug crosses a module boundary).',
      'STYLE: SWE-bench multi-file fault localization. SYMPTOM observed via invoice.total/tax_total (invoice.py); ROOT CAUSE in money.py rounding.',
      'Stdlib only (use the decimal module for exactness). Three modules in gold and broken:',
      '  money.py — function round_cents(exact) -> int: round an exact monetary amount expressed in cents (a decimal.Decimal or float) to the nearest whole cent, ties-to-even (banker\'s rounding). GOLD: use decimal.Decimal(...).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN) and return int. (This file holds the bug.)',
      '  tax.py — function line_tax(amount_cents: int, rate: float) -> int: compute amount_cents * rate as an exact Decimal and return money.round_cents of it. e.g. line_tax(17955, 0.0825) -> 17955*0.0825 = 1481.2875 cents -> 1481.',
      '  invoice.py (FACADE) — class Invoice: add_line(desc, unit_price_cents: int, qty: int, tax_rate: float); subtotal() -> int = sum(unit_price*qty); tax_total() -> int = sum over lines of tax.line_tax(unit_price*qty, rate) (tax computed PER LINE then summed); total() -> int = subtotal + tax_total. Provide a format helper that renders an int-cents value as "$X.YY".',
      'invoice.py must allow: from invoice import Invoice.',
      'GOLD: round_cents does proper ROUND_HALF_EVEN. For a line unit_price_cents=1995, qty=3 -> 5985 cents, rate=0.0825 -> 493.7625 cents -> round to 494.',
      'BROKEN (planted defect, in money.py ONLY): round_cents TRUNCATES via int(exact) (floor toward zero) instead of rounding. So 493.7625 -> 493 (off by one cent), and tax_total/total are a cent low on such lines.',
      'GRADER test_swe08.py (>=8 tests). Include:',
      '  PASS_TO_PASS (gold AND broken): subtotal of mixed lines; a line whose exact tax is already a whole number of cents (e.g. rate that yields an integer) so truncation and rounding agree; the "$X.YY" formatter for a few values; empty invoice totals are 0.',
      '  FAIL_TO_PASS (gold true, broken false): a line whose exact tax has a fractional-cent part > 0.5 (e.g. 493.7625 -> 494) so the gold rounds up but truncation gives 493; tax_total and total reflect the rounded value; and a documented exact tie value rounds half-to-even (e.g. 2.5 cents -> 2, 3.5 cents -> 4) — only assert the tie cases that the gold rule fixes.',
      '  Use exact integer-cent equality. Add the advisory code_quality test.',
    ].join('\n'),
  },

  // ===================== COMPLEX (spec-density traps, large library) =====================
  {
    id: 'c07_migration_runner', cat: 'complex', short: 'c07', weight: 5, module: 'migrator.py', cli: false,
    packages: ['SQLAlchemy'], exemplar: 'complex/c01_job_queue_sqla',
    brief: [
      'TITLE: SQLAlchemy schema-migration runner (integer-vs-string version ordering trap).',
      'STYLE: spec-density trap on a large library. Read c01_job_queue_sqla first and mirror its in-process SQLAlchemy 2.0 + in-memory SQLite approach and per-entrypoint tests.',
      'Create (gold and broken) at least TWO modules so it is genuinely multi-file, e.g. migrations.py (the Migration type) and migrator.py (the FACADE).',
      '  migrations.py — class Migration with attributes version: int, name: str, and two callables up(conn) and down(conn) that execute DDL/DML via a SQLAlchemy Connection (use conn.execute(text(...))).',
      '  migrator.py (FACADE) — class Migrator(engine): a SQLAlchemy Engine is passed in. On first use it ensures a schema_versions table exists (columns: version INTEGER PRIMARY KEY). Methods:',
      '     register(migration): add to the known set; raise ValueError on a duplicate version.',
      '     applied_versions() -> list[int]: the applied versions, sorted ASCENDING as INTEGERS, read from schema_versions.',
      '     current() -> int | None: the max applied version (None if none).',
      '     upgrade(target: int | None = None): apply every registered migration whose version > current(), in ASCENDING integer order, up to and INCLUDING target (target=None means apply all). Each migration runs inside a transaction (begin/commit); on success insert its version row in the SAME transaction. Idempotent: a second upgrade() with nothing pending is a no-op.',
      '     downgrade(target: int): roll back every applied migration whose version > target, in DESCENDING integer order, calling down() and deleting its version row, each in a transaction. target may be below the lowest version (roll back all).',
      '     A migration whose up() raises must roll back its transaction so its version is NOT recorded and its partial changes are undone; the exception propagates.',
      'migrator.py must allow: from migrator import Migrator, Migration.',
      'GOLD: ordering is by INTEGER version everywhere. Register order-dependent migrations: v2 creates a table widgets(id INTEGER PRIMARY KEY, qty INTEGER), v10 runs `ALTER TABLE widgets ADD COLUMN price INTEGER` (or inserts depending on v2 table). upgrade() applies v2 THEN v10 regardless of registration order. With versions 2 and 10 present, applied_versions()==[2,10] and current()==10.',
      'BROKEN (planted defect): version ordering uses STRING/lexicographic sort instead of integer — e.g. upgrade sorts pending migrations by str(version) and current()/applied_versions() compute max/sort over the string form. With versions 2 and 10, "10" < "2" lexically, so v10 is applied BEFORE v2 -> v10\'s ALTER fails because widgets does not exist yet (or applied_versions() returns the wrong order / current() returns 2). The bug only manifests once a version >= 10 coexists with a single-digit version.',
      'GRADER test_c07.py (mirror c01: many small per-method tests for partial credit, >=10). Include:',
      '  PASS_TO_PASS (gold AND broken): register + duplicate-version ValueError; a fresh Migrator has current() None and applied_versions() []; upgrading a single migration records it; idempotent re-upgrade applies nothing; downgrade of a single migration; a migration whose up() raises leaves it unrecorded (use a migration with a version < 10 so the ordering bug does not interfere) and rolls back partial changes.',
      '  FAIL_TO_PASS (gold true, broken false): with versions 2 and 10 registered (in REVERSED registration order, 10 then 2), upgrade(None) leaves the schema fully migrated and applied_versions()==[2,10] and current()==10; downgrade(2) then upgrade() round-trips correctly. (Under the string-sort bug the v10-before-v2 application errors or yields wrong order.)',
      '  Build the Engine with create_engine("sqlite://") (in-memory, single connection) or a temp file; mirror c01 for the exact 2.0 idioms. Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'c08_pivot_report', cat: 'complex', short: 'c08', weight: 5, module: 'report.py', cli: false,
    packages: ['pandas', 'numpy'], exemplar: 'complex/c03_graph_engine',
    brief: [
      'TITLE: Pandas pivot/report engine (missing-combination fill and tie-break spec-density traps).',
      'STYLE: spec-density trap on pandas. Multi-file: e.g. frame.py (build/validate the DataFrame) and report.py (FACADE).',
      '  frame.py — function build_frame(records: list[dict]) -> pandas.DataFrame: construct a DataFrame from a list of row dicts; raise ValueError if records is empty.',
      '  report.py (FACADE) — class Report(records): builds the frame via frame.build_frame. Methods:',
      '     pivot(index: str, columns: str, value: str, agg: str) -> pandas.DataFrame: a pivot table (pandas.pivot_table) of value aggregated by agg ("sum" or "count") over index x columns. EVERY missing (index, column) combination MUST be filled with 0 (integer), NOT NaN. For agg=="count" and agg=="sum" the cell dtype MUST be a Python/NumPy integer (no floats, no NaN). Columns sorted ascending; index sorted ascending.',
      '     totals(index, columns, value, agg) -> pandas.DataFrame: the same pivot plus a row labelled "Total" and a column labelled "Total" holding the marginal sums (use that EXACT label, not pandas\' default "All").',
      '     top_n(index: str, value: str, n: int) -> list[tuple]: group by index, SUM value, return the top n as (index_label, total) tuples sorted by total DESCENDING, ties broken by index_label ASCENDING.',
      'report.py must allow: from report import Report.',
      'GOLD: pivot fills absent combos with 0 and keeps integer dtype; totals uses the label "Total"; top_n breaks ties by ascending index label.',
      'BROKEN (planted defect): pivot omits fill_value=0 so missing combinations come back as NaN (and the column dtype becomes float). Pick exactly ONE clear defect — the NaN-instead-of-0 fill — so the FAIL_TO_PASS test (a known-missing combo equals 0 with integer dtype) fails while present-combo values still match.',
      'GRADER test_c08.py (>=10 tests). Build a small fixed list of record dicts inline (deterministic). Include:',
      '  PASS_TO_PASS (gold AND broken): present (index,column) combos have the correct aggregated value; top_n returns the right top entries when there is no tie; totals marginal sums are correct.',
      '  FAIL_TO_PASS (gold true, broken false): a (index,column) combination that does not occur in the data has value 0 (use gu.close or == 0) and the pivot has NO NaN (assert not result.isna().any().any()) and an integer dtype; totals row/col are labelled exactly "Total"; top_n with a deliberate tie returns the tied entries ordered by ascending index label.',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },

  // ===================== EASY (spec-density trap) =====================
  {
    id: 'e06_semver_order', cat: 'easy', short: 'e06', weight: 1, module: 'solution.py', cli: true,
    packages: ['stdlib'], exemplar: 'easy/e01_csv_pulse',
    brief: [
      'TITLE: Semantic-version precedence (SemVer 2.0.0) — dense rule set, numeric-vs-alphanumeric pre-release trap.',
      'STYLE: spec-density trap, single file solution.py, stdlib only.',
      'Public contract:',
      '  parse(version: str) -> dict with keys major, minor, patch (ints), prerelease (list[str], may be empty), build (list[str], may be empty). Raise ValueError on a malformed version (missing parts, non-numeric core, empty identifiers).',
      '  compare(a: str, b: str) -> int returning -1, 0, or 1 by SemVer 2.0.0 precedence:',
      '     * compare major, then minor, then patch numerically;',
      '     * a version WITH a pre-release has LOWER precedence than the same version WITHOUT one (1.0.0-alpha < 1.0.0);',
      '     * compare pre-release identifiers left to right: identifiers consisting only of digits compare NUMERICALLY; identifiers with letters compare lexically in ASCII order; a numeric identifier always has LOWER precedence than an alphanumeric one; if all shared identifiers are equal, the version with MORE identifiers has higher precedence;',
      '     * BUILD metadata is IGNORED for precedence (1.0.0+build1 == 1.0.0+build2 == 1.0.0).',
      '  sort_versions(versions: list[str]) -> list[str]: ascending by precedence; build metadata preserved in the returned strings but irrelevant to ordering; equal-precedence versions keep input order (stable).',
      'CLI contract:  python solution.py compare A B  prints -1/0/1 and exits 0;  python solution.py sort V1 V2 ...  prints the sorted versions one per line. On a malformed version print an error to stderr and exit non-zero.',
      'GOLD: implements every rule above, especially numeric pre-release identifiers compared as integers (so alpha.9 < alpha.11) and build metadata ignored.',
      'BROKEN (planted defect): pre-release identifiers are ALWAYS compared as strings (no numeric handling), so "11" < "9" lexically and compare("1.0.0-alpha.9","1.0.0-alpha.11") wrongly returns 1.',
      'GRADER test_e06.py (>=8 tests). Include:',
      '  PASS_TO_PASS (gold AND broken): core numeric ordering (1.0.0 < 1.0.1 < 1.1.0 < 2.0.0); 1.0.0-alpha < 1.0.0; build metadata ignored (1.0.0+x == 1.0.0); equal versions compare 0; parse() rejects a malformed version with ValueError; the CLI compare path.',
      '  FAIL_TO_PASS (gold true, broken false): compare("1.0.0-alpha.9","1.0.0-alpha.11") == -1 (numeric identifier ordering); a sort that places alpha.2 < alpha.10; numeric-identifier < alphanumeric-identifier (1.0.0-1 < 1.0.0-alpha).',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },

  // ===================== COMPOSITIONAL (>=3 libraries + exception paths) =====================
  {
    id: 'cb05_config_validator', cat: 'compositional', short: 'cb05', weight: 4, module: 'solution.py', cli: false,
    packages: ['pyyaml'], exemplar: 'compositional/cb01_log_analytics',
    brief: [
      'TITLE: YAML config validator with canonical hashing — composes yaml + re + json + hashlib, full exception-path coverage.',
      'STYLE: BigCodeBench-style multi-library composition with precise, ordered exception types. Single file solution.py.',
      'Compose at least THREE stdlib/3rd-party libraries: yaml (PyYAML, safe_load), re (regex patterns), json (canonical serialization), hashlib (sha256). (re + json + hashlib are stdlib; yaml is the 3rd-party one.)',
      'Public contract:',
      '  validate_config(yaml_text: str, schema: dict) -> dict.',
      '  schema maps each key name -> a rule dict that may contain: "type" in {"int","float","str","bool","list"} (required field of the rule), "required" (bool, default False), "default" (used when the key is absent and not required), "pattern" (regex string, only for type str), "min"/"max" (numeric bounds for int/float).',
      '  Algorithm: yaml.safe_load the text into a mapping; process keys in SORTED order; build a validated dict; then return it with an added key "_hash" whose value is the sha256 hex digest of json.dumps(validated_without_hash, sort_keys=True, separators=(",",":")).encode().',
      '  EXCEPTION CONTRACT (types and PRECEDENCE — assert types only, never messages):',
      '     * yaml.safe_load failing, or a result that is not a mapping -> raise ValueError.',
      '     * a key that is required and absent (and has no default) -> raise KeyError. This check happens BEFORE any type/constraint check.',
      '     * a present value whose Python type does not match the rule type (bool is NOT an int here) -> raise TypeError.',
      '     * a str value failing its "pattern", or a numeric value outside [min,max] -> raise ValueError.',
      '     * precedence per key: required(KeyError) > type(TypeError) > constraint(ValueError).',
      '  Absent keys with a default are filled with the default WITHOUT type-checking the default.',
      'GOLD: implements the precedence exactly — the required-presence check precedes the type check, so a missing required key raises KeyError.',
      'BROKEN (planted defect): for a missing required key the code first substitutes None (as if a default) and then runs the type check, raising TypeError instead of KeyError. So the required-key path raises the WRONG exception type.',
      'GRADER test_cb05.py (>=8 tests, heavy on exception paths). Include:',
      '  Happy path: a valid config returns the validated dict with correct coerced values, defaults applied, and a stable "_hash"; the same input twice yields the SAME hash; changing a value changes the hash.',
      '  Exception paths (pytest.raises): invalid YAML -> ValueError; non-mapping YAML (e.g. a top-level list) -> ValueError; wrong type -> TypeError; pattern mismatch -> ValueError; out-of-range number -> ValueError; bool supplied where int expected -> TypeError.',
      '  FAIL_TO_PASS (gold true, broken false): a missing REQUIRED key (no default) raises KeyError (not TypeError).',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'cb06_timeseries_resample', cat: 'compositional', short: 'cb06', weight: 4, module: 'solution.py', cli: false,
    packages: ['pandas', 'numpy', 'scipy'], exemplar: 'compositional/cb01_log_analytics',
    brief: [
      'TITLE: Irregular time-series resampling + robust outliers — composes pandas + numpy + scipy, NaN-handling trap.',
      'STYLE: multi-library composition with a realistic NaN-handling defect. Single file solution.py. Surface-form: must use scipy.stats.zscore.',
      'Public contract:',
      '  resample_clean(readings: list[dict], freq: str) -> dict. Each reading is {"ts": ISO-8601 string, "value": float}.',
      '  Steps: parse ts to a pandas DatetimeIndex; sort ascending; drop duplicate timestamps keeping the LAST; set as a Series; resample to freq taking the MEAN of each bucket; linearly INTERPOLATE internal gaps only (method="linear", limit_area="inside" so leading/trailing NaNs are NOT filled); compute outlier flags with scipy.stats.zscore over the cleaned values using nan_policy="omit", flagging |z| > 3.0; compute mean and std (population-free: numpy with ddof=1) over the NON-NaN values only (use numpy.nanmean / numpy.nanstd).',
      '  Return dict: {"index": [iso strings], "values": [float or None for still-NaN buckets], "outliers": [bool], "n_interpolated": int (count of buckets filled by interpolation), "mean": float, "std": float}.',
      '  EXCEPTION CONTRACT: empty readings -> ValueError; an unparseable ts -> ValueError; an invalid freq -> ValueError; an all-equal-values input must NOT crash (zscore of constant -> treat as no outliers).',
      'GOLD: uses nan_policy="omit" and numpy.nanmean/nanstd, so a leading empty bucket that stays NaN does not poison mean/std/outliers; the known spike is flagged.',
      'BROKEN (planted defect): computes scipy.stats.zscore WITHOUT nan_policy (default "propagate") and uses numpy.mean/std (not nan-aware). When the cleaned series contains a leading NaN bucket (legitimately unfillable), every z becomes NaN so NO outlier is flagged and mean/std come back NaN.',
      'GRADER test_cb06.py (>=8 tests). Build a fixed deterministic readings list inline whose first resample bucket is empty (leading gap that interpolation cannot fill) and which contains one clear spike. Include:',
      '  Happy path: index/values lengths agree; n_interpolated equals the known count; a known mid-series gap is interpolated to the linear midpoint (gu.close); mean and std are finite and match an independent computation over the non-NaN values within tolerance.',
      '  Exception paths: empty -> ValueError; bad ts -> ValueError; bad freq -> ValueError; constant-value input returns no outliers and a finite mean.',
      '  Surface-form: gu.source_uses(SOL, ["scipy.stats.zscore"]) or ["zscore"] is present.',
      '  FAIL_TO_PASS (gold true, broken false): with the leading-empty-bucket dataset, mean is finite (not NaN) AND the known spike bucket is flagged True in outliers. (Under the propagate bug both fail.)',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'cb07_graph_spectral', cat: 'compositional', short: 'cb07', weight: 4, module: 'solution.py', cli: false,
    packages: ['networkx', 'scipy', 'numpy'], exemplar: 'compositional/cb04_linalg_solver',
    brief: [
      'TITLE: Graph Laplacian spectral partition — composes networkx + scipy.linalg + numpy, Fiedler-index trap.',
      'STYLE: multi-library composition cross-checked against an INDEPENDENT networkx reference. Single file solution.py. Read cb04_linalg_solver first for the numpy/scipy.linalg idioms.',
      'Public contract:',
      '  spectral_partition(edges: list[tuple], n: int) -> dict. edges are (u, v, w) with 0 <= u,v < n and positive weight w on an undirected graph with n nodes (isolated nodes allowed).',
      '  Build a networkx.Graph with all n nodes (add_nodes_from(range(n))) and the weighted edges; form the combinatorial Laplacian L = D - A as a dense numpy array (networkx.laplacian_matrix(...).toarray() with a fixed nodelist=range(n)); compute its eigenvalues/eigenvectors with scipy.linalg.eigh (symmetric); sort ascending.',
      '  Return {"fiedler_value": float (the SECOND-smallest eigenvalue == algebraic connectivity), "partition": list[int] of length n giving 0/1 by the sign of the corresponding entry of the Fiedler vector (entry >= 0 -> 0 else 1), "connected": bool (the graph is connected iff the second-smallest eigenvalue > 1e-8), "n_components": int (number of near-zero eigenvalues, i.e. eigenvalues < 1e-8)}.',
      '  EXCEPTION CONTRACT: n < 1 -> ValueError; an edge referencing a node index outside [0, n) -> ValueError; a non-positive weight -> ValueError.',
      'GOLD: fiedler_value is eigenvalues[1] (the second smallest). For a connected graph this equals networkx.algebraic_connectivity(G, weight="weight") within tolerance and is > 0.',
      'BROKEN (planted defect): returns eigenvalues[0] (the smallest, always ~0) as fiedler_value, so for a connected graph fiedler_value is ~0 instead of the true algebraic connectivity, and "connected" is computed from the wrong eigenvalue (always False).',
      'GRADER test_cb07.py (>=8 tests). Cross-check against networkx independently. Include:',
      '  Happy path on a connected weighted graph (e.g. a path or small mesh): fiedler_value matches networkx.algebraic_connectivity within rtol; partition splits the nodes into two non-empty groups; connected is True; n_components == 1.',
      '  A disconnected graph (two components): connected is False; n_components == 2; fiedler_value ~ 0.',
      '  Exception paths: n < 1 -> ValueError; out-of-range edge endpoint -> ValueError; non-positive weight -> ValueError.',
      '  FAIL_TO_PASS (gold true, broken false): on the connected graph fiedler_value > 1e-6 and equals networkx.algebraic_connectivity within tolerance, and connected is True.',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },

  // ===================== DATA_ANALYSIS (surface-form + statistical twist) =====================
  {
    id: 'd07_paired_design', cat: 'data_analysis', short: 'd07', weight: 3, module: 'solution.py', cli: true,
    packages: ['numpy', 'pandas', 'scipy', 'matplotlib'], exemplar: 'data_analysis/d01_ab_test_report',
    brief: [
      'TITLE: Paired before/after experiment — the DS-1000 twist: the obvious unpaired t-test is WRONG; the contract requires a PAIRED test.',
      'STYLE: data_analysis with a surface-form constraint that breaks the memorized pattern. Read d01_ab_test_report and mirror its data/, analyze(df), CLI, results.json + PNG shape. NOTE: unlike d01 you do NOT need a precomputed expected/ JSON — the grader computes the paired reference inline with scipy. You DO commit the dataset.',
      'Dataset: generate data/paired.csv deterministically (numpy default_rng(seed=...) fixed) with columns subject_id, before, after, where after = before + a positive treatment effect + small noise, designed so the PAIRED test is clearly significant (p far below 0.05) while an UNPAIRED test on the same columns is much weaker (ideally not significant) — this maximises discrimination. Generate it with a one-off script run via python3 and COMMIT the csv. ~40-60 subjects.',
      'Public contract:',
      '  analyze(df: pandas.DataFrame) -> dict with keys: n (int), mean_before (float), mean_after (float), mean_diff (float = mean(after-before)), t_stat (float), p_value (float), cohens_d (float = mean_diff / std of the differences, ddof=1), ci95_low, ci95_high (float, 95% CI of the mean paired difference using the t distribution), reject_null (bool at alpha=0.05).',
      '  The paired test MUST use scipy.stats.ttest_rel(after, before). Surface-form (enforced): scipy.stats.ttest_rel must appear in the source and scipy.stats.ttest_ind must NOT.',
      '  CLI: python solution.py --data <csv> --output-dir <dir> writes results.json (same keys) and TWO PNGs: a histogram of the paired differences and a before-vs-after paired plot.',
      'GOLD: uses ttest_rel; all values correct.',
      'BROKEN (planted defect): uses scipy.stats.ttest_ind(after, before) (unpaired) instead of ttest_rel — t_stat and p_value then differ from the paired reference, and the surface-form test (ttest_rel present, ttest_ind absent) fails.',
      'GRADER test_d07.py (>=8 tests). Load the committed csv; compute the PAIRED reference inline with scipy.stats.ttest_rel; call analyze(df). Include:',
      '  return type + required keys; n correct; mean_before/mean_after/mean_diff correct (these match in both gold and broken — PASS_TO_PASS); reject_null True with p < 0.05.',
      '  FAIL_TO_PASS (gold true, broken false): t_stat matches the inline ttest_rel reference within rtol=1e-3 (the unpaired t differs); p_value matches the paired reference; surface-form gu.source_uses(SOL, ["ttest_rel"]) is True AND ["ttest_ind"] is False.',
      '  CLI writes results.json with matching t_stat and >= 2 valid PNGs (gu.count_valid_pngs >= 2).',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },
  {
    id: 'd08_multiple_comparisons', cat: 'data_analysis', short: 'd08', weight: 3, module: 'solution.py', cli: true,
    packages: ['numpy', 'pandas', 'scipy', 'matplotlib'], exemplar: 'data_analysis/d01_ab_test_report',
    brief: [
      'TITLE: K-group comparison with multiple-comparison correction — the twist: naive pairwise t-tests over-reject; the contract requires Holm-Bonferroni.',
      'STYLE: data_analysis with an omnibus test + family-wise error control. Mirror d01 for data/, analyze(df), CLI, results.json + PNGs. Grader computes references inline (no expected/ JSON). Commit the dataset.',
      'Dataset: generate data/groups.csv deterministically (fixed rng) with columns group in {A,B,C,D} and value. Tune the group means so that the one-way ANOVA is significant AND at least one pair is significant under raw pairwise t-tests but NOT significant after Holm-Bonferroni correction — that specific pair is the discriminator. ~30-40 rows per group.',
      'Public contract:',
      '  analyze(df: pandas.DataFrame) -> dict with keys: group_means (dict label->float), n_per_group (dict label->int), anova_f (float), anova_p (float), omnibus_significant (bool at alpha=0.05), pairs (dict "X_vs_Y"-> {"raw_p": float, "adj_p": float, "significant": bool}) for all C(K,2) unordered pairs in sorted label order, and "n_significant_pairs" (int).',
      '  Method: omnibus via scipy.stats.f_oneway over the groups; pairwise via scipy.stats.ttest_ind (independent, equal_var as you document); adjust the raw p-values with the HOLM-Bonferroni step-down procedure at FWER 0.05; a pair is significant iff its Holm-adjusted p < 0.05. Surface-form (enforced): scipy.stats.f_oneway must appear in the source.',
      '  CLI: python solution.py --data <csv> --output-dir <dir> writes results.json (same keys) and TWO PNGs: group means with error bars, and a pairwise adjusted-p heatmap/matrix.',
      'GOLD: applies the Holm correction; the discriminator pair is NOT significant after adjustment.',
      'BROKEN (planted defect): skips the correction entirely — sets adj_p = raw_p (or declares significance from raw_p), so the discriminator pair is wrongly marked significant and n_significant_pairs is too high.',
      'GRADER test_d08.py (>=8 tests). Load the committed csv; compute the ANOVA and the Holm-corrected pairwise references inline with scipy + a hand-written Holm step. Include:',
      '  return type + keys; group_means and n_per_group correct (PASS_TO_PASS); anova_f and anova_p match the inline f_oneway reference; omnibus_significant True.',
      '  FAIL_TO_PASS (gold true, broken false): the discriminator pair adj_p > raw_p AND its "significant" flag is False (matching the Holm reference); n_significant_pairs equals the corrected count (which is LOWER than the raw count); surface-form f_oneway present.',
      '  CLI writes results.json and >= 2 valid PNGs.',
      '  Add the advisory code_quality test.',
    ].join('\n'),
  },

  // ===================== LONG_HORIZON (state cascades, provenance) =====================
  {
    id: 'lh11_index_build', cat: 'long_horizon', short: 'lh11', weight: 3, steps: 6, module: 'solution.py', cli: true,
    packages: ['stdlib'], exemplar: 'long_horizon/lh01_two_step_tally',
    brief: [
      'TITLE: 6-step TF-IDF search-index pipeline — a wrong document-frequency in step 3 cascades through ranking.',
      'STYLE: long_horizon state cascade. Read lh01_two_step_tally and mirror EXACTLY: solution.py dispatches on --step K --in <prev> --out <out>; each step writes JSON {"step":k,"data":<result>,"provenance": sha256 hex of the file it read}; step k reads ONLY step k-1\'s artifact (step 1 reads the committed seed). Stdlib only.',
      'Seed: commit data/docs.json = {"docs": [{"id":"d1","text":"..."}, ...]} — a small fixed corpus of ~6 short documents with deliberate term overlap so ranking is non-trivial.',
      'Steps (each reads prev["data"] except step 1 which reads prev["docs"]):',
      '  1 tokenize: lowercase each doc text and split on runs of non-alphanumeric chars; data = {doc_id: [tokens]}.',
      '  2 term_counts: data = {doc_id: {term: count}} from step 1.',
      '  3 doc_frequency: data = {term: number_of_DOCUMENTS containing term} (a document counts once regardless of repeats). THIS is where the bug goes.',
      '  4 tfidf: data = {doc_id: {term: tf * idf}} where tf = count/total_terms_in_doc and idf = log(N / df[term]) with N = number of docs and natural log; round to 6 decimals for stability.',
      '  5 rank_query: a FIXED query is embedded in the step-5 code (e.g. the constant QUERY = ["alpha","beta"] chosen from the corpus). data = list of [doc_id, score] sorted by descending cosine similarity between the query vector (tf-idf weighted, query term tf=1) and each doc tf-idf vector; ties broken by doc_id ascending; scores rounded to 6 decimals.',
      '  6 top_k: data = {"top": [doc_id, ...] first 3 ids from step 5, "scores": [the 3 scores]}.',
      'GOLD: step 3 computes true document frequency (each doc contributes at most 1 per term).',
      'BROKEN (planted defect, step 3 ONLY): doc_frequency sums the term COUNTS across docs (total occurrences) instead of the number of documents — so df is inflated for repeated terms, idf is wrong, and steps 4,5,6 cascade to wrong tfidf and ranking.',
      'GRADER test_lh11.py: mirror lh01 — use gu.run_provenance_chain(SOL, data/docs.json, 6, tmp) and compare each step\'s data to a canonical reference. PRECOMPUTE the reference by RUNNING the GOLD chain and capturing each step\'s data into expected/steps.json keyed "1".."6" (do NOT hand-write the numbers). One parametrized test per step asserting ran + prov_ok + data matches expected (use a recursive gu.close comparison like lh01\'s _approx_equal for the float maps), plus a final cumulative test asserting the top-3 ids/scores. Add the advisory code_quality test.',
      'Because the bug is in step 3, the gold passes all 6 step tests while the broken fails steps 3-6 (partial credit tracks steps 1-2 surviving).',
    ].join('\n'),
  },
  {
    id: 'lh12_budget_forecast', cat: 'long_horizon', short: 'lh12', weight: 4, steps: 8, module: 'solution.py', cli: true,
    packages: ['numpy'], exemplar: 'long_horizon/lh01_two_step_tally',
    brief: [
      'TITLE: 8-step budget forecast — a reversed cumulative balance in step 4 cascades into the trend and projection.',
      'STYLE: long_horizon state cascade, 8 steps (a longer chain = higher weight and more cascade surface). Mirror lh01 exactly (--step/--in/--out, {"step","data","provenance"} per step, prev-feeds-forward). numpy is allowed for the least-squares fit; otherwise stdlib.',
      'Seed: commit data/transactions.json = {"transactions": [{"date":"YYYY-MM-DD","amount": float,"category": str}, ...]} — a fixed multi-month set (~6-8 distinct months) of income and expense rows with a clear linear trend in monthly net.',
      'Steps (each reads prev["data"] except step 1 reads prev["transactions"]):',
      '  1 parse_sort: data = list of txns sorted ascending by date (ISO date strings sort lexically).',
      '  2 sign_normalize: data = same list with a normalized signed "net" per txn — income categories positive, expense categories negative (define a small fixed category->sign map in code; unknown category treated as expense).',
      '  3 monthly_net: data = {"YYYY-MM": net_sum} aggregated per calendar month (a dict).',
      '  4 cumulative_balance: data = list of [month, running_balance] in ASCENDING month order, running balance = cumulative sum of monthly nets from earliest to latest. THIS is where the bug goes.',
      '  5 trend_fit: fit a line balance ~ slope*month_index + intercept over the ascending months (month_index 0,1,2,...) via numpy.polyfit(deg=1); data = {"slope":..,"intercept":..} rounded to 6 decimals.',
      '  6 project: data = list of [future_month_index, projected_balance] for the next 3 month indices using the fitted line; rounded.',
      '  7 scenario: apply a fixed scenario adjustment (e.g. multiply each projected balance by 1.10 to model a +10% savings scenario); data = adjusted [index, value] list, rounded.',
      '  8 summary: data = {"final_balance": last adjusted projected balance, "slope": step5 slope, "n_months": number of historical months}, rounded.',
      'GOLD: step 4 accumulates from EARLIEST to latest month in ascending order.',
      'BROKEN (planted defect, step 4 ONLY): accumulates in DESCENDING month order (or reverses the month list before cumsum), so the running balances are wrong, which corrupts the slope/intercept in step 5 and everything downstream (6,7,8).',
      'GRADER test_lh12.py: mirror lh01 — gu.run_provenance_chain(SOL, data/transactions.json, 8, tmp); PRECOMPUTE expected/steps.json by RUNNING the GOLD chain (keys "1".."8"); one parametrized per-step test (ran + prov_ok + data matches via recursive gu.close), plus a final cumulative test on final_balance and slope. Add the advisory code_quality test.',
      'Gold passes all 8; broken fails steps 4-8 while steps 1-3 survive (partial credit).',
    ].join('\n'),
  },
]

function briefText(s) {
  const ep = 'entrypoints module = "' + s.module + '", cli = ' + (s.cli ? 'true' : 'false') +
    (s.steps ? ', steps = ' + s.steps : ', steps = null')
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
      ? ('A previous attempt reported NOT-valid. Its summary: gold="' + (res.gold_summary || '?') +
         '" broken="' + (res.broken_summary || '?') + '" notes="' + (res.notes || '') + '". ')
      : 'A previous attempt failed to produce a usable result. '
    return agent(
      PREAMBLE + '\n' + briefText(s) + '\n' + VERIFY(s) +
      '\n\nREPAIR MODE: ' + ctx +
      'Re-read the files already on disk for this task, run BOTH verification commands yourself, diagnose the real cause, ' +
      'and fix whichever of {gold, grader, broken, data, expected} is wrong until gold is fully green AND broken has >=1 failure. ' +
      'Then return the structured result with ok set from what you actually observed.',
      { label: 'repair:' + s.id, phase: 'Repair', schema: SCHEMA })
  },
)

const ok = results.filter((r) => r && r.ok)
const bad = results.filter((r) => !r || !r.ok)
log('Authoring complete: ' + ok.length + '/' + SPECS.length + ' tasks self-checked valid.')
if (bad.length) log('NOT valid: ' + bad.map((r, i) => (r && r.id) || SPECS[i] && SPECS[i].id).join(', '))
return { valid: ok.map((r) => r.id), invalid: bad.map((r) => r && r.id), results }
