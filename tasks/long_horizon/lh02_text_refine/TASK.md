# Long-Horizon 02 — `text_refine` (4 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 4 steps · **Weight:** 2

Build a **4-step text-processing pipeline** as a single file `solution.py`. Each
step is run separately and **consumes only the artifact written by the previous
step** — you may not re-read the original input from a later step.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out` a
JSON object with **exactly** these keys:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path,'rb').read()).hexdigest()`. The
grader verifies it, so step *K* must genuinely read the file produced by step
*K-1*.

## The chain

**Input** (`data/input.json`, given):
```json
{"text": "The Quick brown Fox, the QUICK fox! The fox runs."}
```

* **Step 1 — `normalize`:** Read `prev["text"]`. Lowercase the string, then
  replace every character that is **not** an ASCII letter or a space with a
  single space.
  Produce `data: <resulting string>`.
  (Example: `"The Quick brown Fox, the QUICK fox! The fox runs."` →
  `"the quick brown fox  the quick fox  the fox runs "`)

* **Step 2 — `tokenize`:** Read `prev["data"]` (the normalized string from step
  1). Split on whitespace and drop empty tokens.
  Produce `data: <list of str>`.
  (Example: `["the", "quick", "brown", "fox", "the", "quick", "fox", "the",
  "fox", "runs"]`)

* **Step 3 — `count`:** Read `prev["data"]` (the token list from step 2). Count
  occurrences of each unique token (case-sensitively on the already-lowercased
  tokens — all tokens are already lowercase at this point).
  Produce `data: <dict mapping word → int count>`.
  (Example: `{"the": 3, "quick": 2, "brown": 1, "fox": 3, "runs": 1}`)

* **Step 4 — `top_k`:** Read `prev["data"]` (the count dict from step 3). Return
  the top **3** entries by count descending; break ties by word ascending
  (alphabetical). Each entry is a two-element list `[word, count]`.
  Produce `data: <list of [word, count] pairs, length ≤ 3>`.
  (Example: `[["fox", 3], ["the", 3], ["quick", 2]]`)

Because each step reads the previous step's output, an error in any early step
cascades into all later steps.

## Notes

* **Standard library only** (`argparse`, `hashlib`, `json`, `re`, `collections`,
  etc.). No third-party packages.
* Deterministic. The grader checks each step's `data` field against a fixture.
* Step 1's `--in` is `data/input.json`; step K's `--in` is step K-1's `--out`.
