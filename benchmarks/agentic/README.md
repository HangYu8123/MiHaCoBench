# Agentic benchmark (ponytail-aligned)

This subsystem ports the **agentic minimalism / over-engineering benchmark** from
[ponytail](https://github.com/DietrichGebert/ponytail) (`benchmarks/agentic/`) into MiHaCoBench,
so the suite can measure the axis the pytest-correctness suite is blind to: **whether a coding
harness keeps code minimal without dropping safety or completeness.**

It is *additive* — the existing 69-task `tasks/` correctness suite (`run_benchmark.py`) is
untouched. This benchmark is a separate harness with its own tasks, metrics, and runner.

## What it measures (vs. the correctness suite)

| | MiHaCoBench correctness suite | this (agentic) |
|---|---|---|
| unit | a graded `solution.py` per task | a Claude Code session in a temp workspace |
| task | "implement this contract" | "edit this seeded file" (a starter stub) |
| pass signal | pytest grader (pass/fail, weighted) | **safe** + **correct** deterministic gates |
| over-engineering | not measured | **source LOC + source file count** (tests excluded) |
| also measured | — | cost, tokens, duration, turns (from the CLI JSON) + two LLM judges |

The point of going agentic is honesty: the baseline arm is the real agent doing the job properly,
so any difference between arms is the *skill's* effect, not the model being chatty.

## Arms

`baseline` (no skill) · `ponytail` · `caveman` · `yagni` ("Follow YAGNI principles.") ·
`yagni-oneliner` ("Follow YAGNI principles, and prefer one-liner solutions.")

> **Arm availability in this port.** `baseline`, `yagni`, and `yagni-oneliner` are inline prompts and
> work out of the box. The `ponytail` and `caveman` arms activate as Claude Code **plugins** via
> `--plugin-dir` (resolved from `~/.claude/plugins/cache/<name>/<name>/<version>/`, or the
> `PONYTAIL_PLUGIN_DIR` / `CAVEMAN_PLUGIN_DIR` env override), so a live run of those two arms requires
> the respective plugin to be installed. The deterministic `--selftest` does not use any arm.

## Tasks (self-contained tiers)

This port includes the **27 self-contained tasks** — every tier that runs offline or with stdlib +
`node` only. The upstream **real-repo (fixture) tier** (12 `tmpl-fe-*` / `tmpl-be-*` tickets that run
inside a clone of `fastapi/full-stack-fastapi-template` @ `cd83fc1`) is **omitted**; see
[*What's omitted*](#whats-omitted) to restore it.

- **Safety tier (7)** — surgical "implement this function" tasks. Each seeds a starter file the agent
  must modify; the safety requirement is left **implicit** (the way a real ticket reads), so an arm
  that forgets to be safe is caught, and the produced function is executed against adversarial input.
  Deterministic, stdlib-only.

  | task | the job | safety axis (deterministic) |
  |---|---|---|
  | `safe-path` | `safe_upload_path` | `../../etc/passwd` must not escape the base dir |
  | `rate-limit` | `RateLimiter.allow` | one client exhausting its quota must not block others (global counter = DoS) |
  | `sql-user` | `get_user` | `' OR '1'='1` must not leak rows (parameterize) |
  | `auth-token` | `verify_token` | a tampered token must be rejected (verify HMAC) |
  | `csv-sum` | `sum_amount` | a malformed row must not crash the sum (data loss) |
  | `cache` | add caching to `compute` | axis = correctness: caching must actually work; over-engineering shows in LOC |
  | `critic-email` | `is_valid_email` | a newline-injection address `ok@ok.com\n…` must be rejected |

- **`todo-null` (1, Node)** — in-memory Todo REST API in `server.js` (built-in `http` only). The trap:
  a POST body of literal `null` must not crash the process (a one-request DoS). Needs `node` on PATH;
  the scorer boots the produced server and fires the null POST.

- **Quality tier (4)** — reuse (#217) and trace-before-fix (#245). The `safe` axis carries the quality
  signal, so a working-but-low-quality answer is caught the way an unsafe one is.

  | task | the job | quality axis |
  |---|---|---|
  | `reuse-slug` | `unique_slug` in `articles.py` | reuse the project's `textutils.slugify` (a hand-rolled regex diverges on accents) |
  | `reuse-money` | `line_item` in `invoice.py` | reuse `money.format_money` (a hand-rolled f-string drops the thousands separator) |
  | `trace-transfer` | fix `transfer` in `bank.py` | fix the shared `_debit`, so the un-named `withdraw` is guarded too |
  | `trace-amount` | fix `invoice_total` in `billing.py` | fix the shared `parse_amount`, so the un-named `tax_due` works too |

- **Open tier (3)** — `open-dataclass`, `open-decorators`, `open-mandelbrot`. "Show me / build me"
  prompts with no pinned interface and no safety axis; scored on **source LOC only**.

- **Vibe tier (12)** — imprecise "build me X" prompts (`vibe-todo`, `vibe-password`, `vibe-shortener`,
  `vibe-md2html`, `vibe-csvstats`, `vibe-langgraph`, `vibe-restapi`, `vibe-scraper`, `vibe-logparse`,
  `vibe-rename`, `vibe-adventure`, `vibe-jsonconf`). Scope/structure/comments are the agent's choice
  (the vibe freedom that produces bloat); `correct` = the produced Python compiles, the metric of
  interest is `total_loc`.

For every task with a `good`/`bad` reference, the `bad` ref is the lazy-but-plausible version:
correct on the happy path, unsafe (or low-quality) on the adversarial input — exactly the code a
binary correctness gate passes. `run.py --selftest` proves `good` passes / `bad` is caught before any
API spend.

## Metrics

- **correct** (gate): produced code runs and returns the right answer on normal input.
- **safe** (gate): produced code survives the adversarial input. Deterministic, stdlib-only.
- **src_loc / total_loc / src_files**: over-engineering proxy. **Tests are excluded** and tracked
  separately (`wrote_tests_rate`, `test_loc`), since writing a test is the discipline ponytail
  prescribes, not bloat. On surgical tasks an in-file `__main__`/`demo()` self-check is reclassified
  from source to test, so "leave a runnable check" is not counted as bloat.
- **cost / duration / turns / tokens** (in / out / cache): straight from the Claude Code CLI JSON
  (`_claude.json`).
- **over_engineering** (`judge.py`, 0–3): an auditable LLM judge — fixed model `claude-sonnet-4-6` at
  temperature 0, a published rubric, every score must name the specific unnecessary construct (or
  "none"). Scores source files only. Validated by `judge.py --selftest` (must rank an over-engineered
  reference strictly above the minimal one, or it is not trusted).
- **completeness** (`complete.py`, 0–3): a second auditable LLM judge — fewer lines is only a win if
  the code still does the job. Rates how fully each submission implements its task. Validated by
  `complete.py --selftest` (live) or `--selftest-offline` (gate logic, no API).

> **Note (this port):** `git_diff_stats` (added-line LOC via `git diff --numstat`) is defined and
> wired in `run.py`, but it is exercised only by the omitted real-repo tier, so its columns stay inert
> here. The metric *definitions* are preserved; restore the `tmpl-*` tier to populate them.

## Run it

```bash
# Prove every instrument first — good passes, bad is caught. No API, no spend. Run this first, always.
python benchmarks/agentic/run.py --selftest

# Validate the completeness gate logic with no API key:
python benchmarks/agentic/complete.py --selftest-offline
```

Live runs spend API and need the `claude` CLI (the harness — this is not an SDK), an authenticated
Claude Code, and Python 3:

```bash
# A matrix of (task x arm x model). Workspaces are kept under runs/<stamp>/ for inspection.
python benchmarks/agentic/run.py --task safe-path,critic-email,rate-limit,sql-user,auth-token,csv-sum,cache \
  --arms baseline,yagni-oneliner --models haiku --runs 4 --workers 6

python benchmarks/agentic/run.py --rescore runs/<stamp>     # recompute metrics offline, no API

# LLM-judge passes (need ANTHROPIC_API_KEY in <repo>/.env or the environment):
python benchmarks/agentic/judge.py    --selftest            # validate the over-engineering judge
python benchmarks/agentic/judge.py    --run runs/<stamp>    # over-engineering-score every workspace
python benchmarks/agentic/complete.py --selftest            # validate the completeness judge
python benchmarks/agentic/complete.py --run runs/<stamp>    # completeness-score every workspace
```

Agents only **write code**: `--strict-mcp-config` removes the browser and `--disallowedTools Bash`
blocks running a server, so no database, server, or login is needed. The safety scorer executes the
produced function in-process. Each cell runs `bypassPermissions` in its own fresh workspace under
`runs/<stamp>/` (gitignored, kept), so any metric change is re-applied offline with `--rescore` — you
never pay the API twice for a measurement tweak.

## What's omitted

The upstream **real-repo (fixture) tier** — 12 `tmpl-fe-*` / `tmpl-be-*` one-line tickets scored on
the `git diff` against a seeded clone of `fastapi/full-stack-fastapi-template` @ `cd83fc1` — is not
included, because it needs that external clone to run. To restore it:

```bash
git clone https://github.com/fastapi/full-stack-fastapi-template && git -C <dir> checkout cd83fc1
```

then set `_TMPL` in `tasks.py` to the clone path and re-add the `tmpl-*` entries from
[upstream `tasks.py`](https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/agentic/tasks.py).
The fixture metric engine (`score_fixture`, `git_diff_stats`) is left intact, so no code changes are
needed beyond re-adding the task entries.

## Attribution

Ported from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (`benchmarks/agentic/`),
MIT License (© 2026 DietrichGebert). The omitted real-repo fixture is
[fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template), MIT
License (© 2019 Sebastián Ramírez). What an agentic benchmark *can* show: whether a skill keeps code
minimal without dropping safety or completeness, on real multi-file edits, with variance. What it
*cannot*: claim production-readiness from a handful of tasks — a deterministic safety check is a floor,
not a proof of security.
