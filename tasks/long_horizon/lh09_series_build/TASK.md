# Long-Horizon 09 — `series_build` (18 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 18 steps · **Weight:** 9

Build an **18-step numeric pipeline** as a single file `solution.py`. Each step
is invoked separately and **reads only the artifact written by the previous
step** — you may never re-read an earlier artifact from a later step.

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
*K-1* and compute SHA-256 of that file's bytes.

## Input

`data/input.json` (committed):
```json
{"values": [6,13,2,9,18,4,11,7,15,3,20,8,1,16,10,5,19,12,14,17,6,9,13,2]}
```

## The 18-step chain

Step 1 reads `data/input.json`. Each subsequent step reads **only** the previous
step's output artifact. The chain is:

| Step | Name | Operation |
|---|---|---|
| 1 | `parse_float` | Cast every integer in `values` to `float`. Output: `list[float]`. |
| 2 | `double` | Multiply every element by 2. Output: `list[float]`. |
| 3 | `add_const` | Add 2 to every element. Output: `list[float]`. |
| 4 | `cumsum` | Replace with running cumulative sum (left to right). Output: `list[float]`. |
| 5 | `mod` | Replace every element with `v % 13` (Python modulo). Output: `list[float]`. |
| 6 | `scale_by_index` | Multiply every element by its 0-based index: `v[i] *= i`. Output: `list[float]`. |
| 7 | `prefix_max` | Replace with running prefix maximum (left to right). Output: `list[float]`. |
| 8 | `diffs` | Replace with consecutive differences: `[s[1]-s[0], s[2]-s[1], ...]` (length = N-1). Output: `list[float]`. |
| 9 | `abs` | Take the absolute value of every element. Output: `list[float]`. |
| 10 | `filter_gt_mean` | Keep only elements **strictly greater than** the mean of the current list. Output: `list[float]`. |
| 11 | `square` | Square every element (`v**2`). Output: `list[float]`. |
| 12 | `normalize_minmax` | Min-max normalize to `[0, 1]`: `(v - min) / (max - min)`. If all values are equal, output all zeros. Output: `list[float]`. |
| 13 | `scale` | Multiply every element by 100. Output: `list[float]`. |
| 14 | `round3` | Round every element to 3 decimal places. Output: `list[float]`. |
| 15 | `moving_avg_3` | 3-element moving average. For indices 0 and 1, output the original value unchanged. For index i >= 2: `(v[i-2] + v[i-1] + v[i]) / 3`. Output: `list[float]`. |
| 16 | `sort_desc` | Sort the list in descending order. Output: `list[float]`. |
| 17 | `top_k` | Keep only the first 6 elements (top-6 after descending sort); if fewer than 6 elements exist, keep all. Output: `list[float]`. |
| 18 | `aggregate` | Compute `{"sum": <float>, "mean": <float>, "count": <int>, "min": <float>, "max": <float>}` over the list. Output: `dict`. |

## Notes

* `data` field in each step's output must match the type shown above (list or dict).
* Step 1's `--in` is `data/input.json`; step K's `--in` is step K-1's `--out`.
* An error in step K makes step K+1 wrong too — the chain **cascades**.
* Floats compared with tolerance by the grader; do not pre-round intermediate results (except step 14 which explicitly rounds to 3 decimal places).
* `count` in step 18 is an `int`.
* Deterministic. Use stdlib only (`hashlib`, `json`, `argparse`, `math`, etc.).
