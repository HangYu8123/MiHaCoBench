# Long-Horizon 04 — `lh04_ledger_roll` (8 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 8 steps · **Weight:** 4

Build an **8-step pipeline** as a single file `solution.py`.  Each step is run
separately and **consumes only the artifact written by the previous step** — you
may not re-read the original input from a later step.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out` a
JSON object with **exactly** these keys:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path,'rb').read()).hexdigest()`.  The
grader verifies it, so step *K* must genuinely read the file produced by step
*K-1*.

## The chain

**Input** (`data/input.json`, committed):
```json
{"values": [120, -50, -90, 200, -30, -400, 75, -10, 500, -220]}
```

| Step | Name | Operation | Reads from | Output type |
|------|------|-----------|------------|-------------|
| 1 | `parse` | Cast every element of `values` to `float` | `input.json` / `values` key | `list[float]` |
| 2 | `cumsum` | Running cumulative sum of step 1's list | step 1 `data` | `list[float]` |
| 3 | `prefix_min` | Running minimum (min seen so far at each index) of step 2's list | step 2 `data` | `list[float]` |
| 4 | `diffs` | Consecutive differences: `data[i+1] - data[i]` for `i` in `0..len-2` | step 3 `data` | `list[float]` (length = len - 1) |
| 5 | `abs` | Element-wise absolute value of step 4's list | step 4 `data` | `list[float]` |
| 6 | `sort_asc` | Sort step 5's list in ascending order | step 5 `data` | `list[float]` |
| 7 | `dedupe` | Remove duplicate values, **preserving the order** from step 6 (keep first occurrence) | step 6 `data` | `list[float]` |
| 8 | `aggregate` | Compute `{"sum": …, "mean": …, "count": …, "min": …, "max": …}` over step 7's list | step 7 `data` | `dict` |

Because each step reads the previous step's artifact, an error in step *k*
causes all subsequent steps to cascade incorrectly.

## Input-key conventions

- **Step 1:** `--in` is `data/input.json`; read the `"values"` key from the top-level dict.
- **Steps 2–8:** `--in` is the previous step's output file; the list (or dict for step 8) is
  under the `"data"` key of that artifact.

## Output contract

Each step writes a single JSON file whose top-level keys are exactly:

```
step        integer  (the step number K)
data        list[float] for steps 1–7; dict for step 8
provenance  string   (sha256 hex of the consumed --in file bytes)
```

Step 8 `data` dict must have exactly these keys (all numeric):
```
sum    float
mean   float
count  int
min    float
max    float
```

## Notes

- Deterministic; no randomness.
- Floats compared with tolerance in the grader.
- Step 1's `--in` is `data/input.json`; each later step's `--in` is the previous step's `--out`.
