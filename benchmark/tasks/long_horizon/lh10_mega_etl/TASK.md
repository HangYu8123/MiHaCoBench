# Long-Horizon 10 — `mega_etl` (20 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 20 steps · **Weight:** 10

Build a **20-step ETL pipeline** as a single file `solution.py`. Each step is run
separately and **consumes only the artifact written by the previous step** — you
may not re-read earlier artifacts from a later step.

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

`data/input.json` (committed): `{"values": [7,14,3,9,18,5,11,2,16,8,1,19,10,6,13,4,17,12,20,15,3,9,6,11,8,14]}`

## The 20-step chain

Step 1's `--in` is `data/input.json`. Each subsequent step's `--in` is the previous step's `--out`.

| Step | Name | Operation |
|------|------|-----------|
| 1 | `parse` | Read `values` from input; convert each integer to `float`. Result: `list[float]`. |
| 2 | `add_const` | Add `7.0` to every element. Result: `list[float]`. |
| 3 | `double` | Multiply every element by `2`. Result: `list[float]`. |
| 4 | `mod` | Apply modulo `11` to every element (floating-point `%`). Result: `list[float]`. |
| 5 | `scale_by_index` | Multiply each element by its **1-based position** (element at index `i` is multiplied by `i + 1`). Result: `list[float]`. |
| 6 | `cumsum` | Running cumulative sum (element `k` = sum of elements `0..k` inclusive). Result: `list[float]`. |
| 7 | `prefix_max` | Running maximum from left (element `k` = max of elements `0..k`). Result: `list[float]`. |
| 8 | `prefix_min` | Running minimum from **right** (element `k` = min of elements `k..end`). Result: `list[float]`. |
| 9 | `diffs` | Consecutive differences: `result[i] = data[i+1] - data[i]`. Result length = `len(input) - 1`. Result: `list[float]`. |
| 10 | `abs` | Absolute value of every element. Result: `list[float]`. |
| 11 | `square` | Square every element (`x * x`). Result: `list[float]`. |
| 12 | `normalize_minmax` | Min-max normalization to `[0, 1]`: `(x - min) / (max - min)`. If `max == min`, all elements become `0.0`. Result: `list[float]`. |
| 13 | `scale` | Multiply every element by `1000`. Result: `list[float]`. |
| 14 | `round3` | Round every element to **3 decimal places** (`round(x, 3)`). Result: `list[float]`. |
| 15 | `moving_avg_3` | Trailing 3-element moving average. Use a smaller window at boundaries: element `0` stays as-is, element `1` = average of elements `0..1`, element `k >= 2` = average of elements `k-2, k-1, k`. Result: `list[float]`. |
| 16 | `filter_gt_mean` | Keep only elements strictly **greater than** the arithmetic mean of the list. Result: `list[float]`. |
| 17 | `sort_desc` | Sort in descending order. Result: `list[float]`. |
| 18 | `dedupe` | Remove duplicate values (keep first occurrence in the current order). Result: `list[float]`. |
| 19 | `top_k` | Keep the first **5** elements (the 5 largest, since the list is already sorted descending). Result: `list[float]` of length 5. |
| 20 | `aggregate` | Compute summary statistics over the 5 values. Result: a JSON object with keys `sum`, `mean`, `min`, `max` (all `float`) and `count` (int 5). |

## Notes

* All arithmetic uses Python floating-point (no rounding except step 14).
* Floats are compared by the grader with tolerance, so do not add extra rounding.
* An error in any step propagates — steps must read their `--in` artifact faithfully.
* Step 8 (`prefix_min`) scans from right to left: `result[i] = min(data[i], data[i+1], ..., data[n-1])`.
