# Long-Horizon 07 — `stats_cascade` (14 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 14 steps · **Weight:** 7

Build a **14-step numerical pipeline** as a single file `solution.py`. Each step is
run separately and **consumes only the artifact written by the previous step** — you
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

`provenance` is `hashlib.sha256(open(in_path,'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

## Input

`data/input.json` (committed): `{"values": [4, 9, 2, 7, 5, 11, 3, 8, 6, 10, 1, 12, 14, 5, 9, 7, 13, 6]}`

18 integer values.

## The chain

All lists start from the previous step's `data` field.

* **Step 1 — `parse`:** read `values` from input; cast each element to `float`.
  Result: a list of 18 floats.

* **Step 2 — `double`:** multiply every element by 2.
  Result: a list of 18 floats.

* **Step 3 — `square`:** raise every element to the power of 2 (`x * x`).
  Result: a list of 18 floats.

* **Step 4 — `normalize_minmax`:** apply min-max normalization.
  For each `x`: `(x - min) / (max - min)` where `min` and `max` are over the current list.
  Result: a list of 18 floats in [0, 1].

* **Step 5 — `scale`:** multiply every element by 50.
  Result: a list of 18 floats.

* **Step 6 — `round3`:** round every element to 3 decimal places (`round(x, 3)`).
  Result: a list of 18 floats.

* **Step 7 — `moving_avg_3`:** apply a 3-element moving average. For index `i`:
  - `i == 0`: window = `[lst[0]]` (length 1)
  - `i == 1`: window = `[lst[0], lst[1]]` (length 2)
  - `i >= 2`: window = `[lst[i-2], lst[i-1], lst[i]]` (length 3)
  The value is `sum(window) / len(window)`.
  Result: a list of 18 floats.

* **Step 8 — `cumsum`:** compute the running cumulative sum.
  `out[i] = sum(lst[0..i])`.
  Result: a list of 18 floats.

* **Step 9 — `diffs`:** compute consecutive differences.
  `out[i] = lst[i+1] - lst[i]` for `i in 0..len-2`.
  Result: a list of **17** floats (one shorter than step 8).

* **Step 10 — `prefix_min`:** compute the running prefix minimum.
  `out[i] = min(lst[0..i])`.
  Result: a list of 17 floats.

* **Step 11 — `abs`:** take the absolute value of every element.
  Result: a list of 17 floats.

* **Step 12 — `sort_desc`:** sort the list in descending order.
  Result: a list of 17 floats.

* **Step 13 — `top_k`:** keep only the first 8 elements (the top-8 largest, since the
  list is already sorted descending).
  Result: a list of **8** floats.

* **Step 14 — `aggregate`:** compute summary statistics over the 8-element list.
  Result: a **dict** with exactly these keys:
  - `"sum"`: sum of all elements (float)
  - `"mean"`: mean of all elements (float)
  - `"min"`: minimum (float)
  - `"max"`: maximum (float)
  - `"count"`: number of elements (int, must equal 8)

Because each step reads the previous step's output, an error in any step makes all
subsequent steps wrong — the chain **cascades**.

## Notes

* Deterministic. Floats compared with tolerance by the grader.
* Step 1's `--in` is `data/input.json`; each subsequent step's `--in` is the previous
  step's `--out`.
* The result of step K is stored in the `data` field of stepK.json.
* Use standard library only (`json`, `argparse`, `hashlib`, `math`, etc.).
