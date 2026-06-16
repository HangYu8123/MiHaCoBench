# Long-Horizon 12 — `budget_forecast` (8 steps)

**Created:** 2026-06-16 · **Category:** long_horizon · **Horizon:** 8 steps · **Weight:** 4

Build an **8-step budget-forecast pipeline** as a single file `solution.py`. Each
step is run separately and **consumes only the artifact written by the previous
step** — you may not re-read the original input from a later step. `numpy` is
allowed (use it for the least-squares line fit); otherwise the standard library
is enough.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out` a
JSON object with **exactly** these keys:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path,'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

* Step 1's `--in` is `data/transactions.json` and it reads the top-level
  `transactions` list.
* Every later step's `--in` is the previous step's `--out`, and it reads the
  list/dict under that artifact's `"data"` key.

## Input (`data/transactions.json`, given)

```json
{"transactions": [{"date": "YYYY-MM-DD", "amount": <float>, "category": "<str>"}, ...]}
```

A fixed multi-month set of income and expense rows (6 distinct calendar months)
with a clear linear trend in the monthly net.

## Category → sign map (fixed, defined in code)

Income categories are **positive**; every other category — including any
**unknown** category — is treated as an **expense** (negative):

```
income = {"salary", "freelance", "bonus", "interest"}   # positive
everything else (incl. unknown)                          # negative
```

## The 8-step chain

Each `data` payload below is what step *K* writes under `"data"`. Numeric values
are rounded to **6 decimals**.

1. **`parse_sort`** — `data` = the list of transaction rows **sorted ascending by
   `date`** (ISO date strings sort lexically).
2. **`sign_normalize`** — `data` = the same ordered list, each row augmented with a
   signed float `"net"` = `+amount` for income categories, `-amount` otherwise.
3. **`monthly_net`** — `data` = a dict `{"YYYY-MM": net_sum}`: the sum of `net`
   per calendar month (month = first 7 chars of `date`).
4. **`cumulative_balance`** — `data` = a list of `[month, running_balance]` in
   **ascending month order**, where `running_balance` is the cumulative sum of the
   monthly nets **from the earliest month to the latest** (earliest month first).
5. **`trend_fit`** — fit `balance ~ slope * month_index + intercept` over the
   ascending months with `month_index = 0, 1, 2, ...` using
   `numpy.polyfit(idx, balances, 1)`. `data` =
   `{"slope": <float>, "intercept": <float>, "n_months": <int # of historical months>}`.
6. **`project`** — using the fitted line, project the next 3 month indices
   (`n_months, n_months+1, n_months+2`). `data` =
   `{"projection": [[index, projected_balance], ...], "slope": <step-5 slope>, "n_months": <int>}`.
   (`slope` and `n_months` are carried forward so the summary step can report them.)
7. **`scenario`** — apply a fixed **+10% savings scenario**: multiply each
   projected balance by `1.10`. `data` =
   `{"projection": [[index, adjusted_balance], ...], "slope": <step-5 slope>, "n_months": <int>}`.
8. **`summary`** — `data` =
   `{"final_balance": <last adjusted projected balance>, "slope": <step-5 slope>, "n_months": <int>}`.

Because each step reads only the previous artifact, an error in an early step
(e.g. the cumulative balance in step 4) cascades into the trend fit and the whole
projection — the chain **cascades**.

## Notes

* Deterministic. Floats compared with tolerance (never `==`).
* The grader runs the chain step-by-step, checks each step's provenance link, and
  compares each step's `data` to the canonical fixture; a final cumulative test
  checks the forecast `final_balance`, `slope`, and `n_months`.
