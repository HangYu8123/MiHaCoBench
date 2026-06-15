# Long-Horizon 08 — `token_pipeline` (16 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 16 steps · **Weight:** 8

Build a **16-step pipeline** as a single file `solution.py`. Each step is run
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

`provenance` is `hashlib.sha256(open(in_path,'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

## The chain

**Input** (`data/input.json`, given): `{"values": [9,4,15,7,2,18,11,6,13,8,1,16,10,5,19,3,12,17,14,20]}`.

The pipeline applies the following operations in order. Each step reads the
`data` field from the previous step's artifact (except step 1 which reads the
`values` key from the original input):

| Step | Name | Operation |
|------|------|-----------|
| 1 | `parse` | Cast each integer in `values` to `float`. `data` = list of floats. |
| 2 | `add_const` | Add `1` to every element. `data` = list of floats. |
| 3 | `double` | Multiply every element by `2`. `data` = list of floats. |
| 4 | `mod` | Apply `% 5` (Python modulo) to every element. `data` = list of floats. |
| 5 | `scale_by_index` | Multiply each element by its zero-based index `i`. Element `i` becomes `data[i] * i`. `data` = list of floats. |
| 6 | `cumsum` | Replace list with cumulative sums (running totals). `data` = list of floats. |
| 7 | `prefix_max` | Replace list with running prefix maximum. `data` = list of floats. |
| 8 | `diffs` | Replace list with consecutive differences: `[x[1]-x[0], x[2]-x[1], ...]`. Length decreases by 1. `data` = list of floats. |
| 9 | `abs` | Apply `abs()` to every element. `data` = list of floats. |
| 10 | `square` | Square every element (`x * x`). `data` = list of floats. |
| 11 | `normalize_minmax` | Apply min-max normalisation: `(x - min) / (max - min)`. If all values equal, produce all zeros. `data` = list of floats. |
| 12 | `scale` | Multiply every element by `10`. `data` = list of floats. |
| 13 | `round3` | Round every element to 3 decimal places. `data` = list of floats. |
| 14 | `sort_asc` | Sort the list ascending. `data` = list of floats. |
| 15 | `dedupe` | Remove **consecutive** duplicate values (preserve order, keep first). `data` = list of floats. |
| 16 | `aggregate` | Produce a summary dict. `data` = `{"sum": <float>, "mean": <float>, "max": <float>, "min": <float>, "count": <int>}`. |

### Key definitions

- **Step 1** reads `prev["values"]` (the raw input list).
- **Steps 2–16** each read `prev["data"]` (the previous step's result).
- **`scale_by_index`**: zero-based indexing; `result[0] = data[0] * 0`, `result[1] = data[1] * 1`, etc.
- **`cumsum`**: `result[k] = sum(data[0..k])`.
- **`prefix_max`**: `result[k] = max(data[0..k])`.
- **`diffs`**: output length = input length − 1.
- **`normalize_minmax`**: `(x − min(data)) / (max(data) − min(data))`.
- **`round3`**: Python `round(x, 3)` for each element.
- **`dedupe`**: removes consecutive duplicates only (like `itertools.groupby`); the sorted list from step 14 makes this equivalent to deduplication of the whole list.
- **`aggregate`**: `sum`, `mean` (sum/count), `max`, `min`, `count` over the deduplicated list.

Because each step reads the prior step's artifact, an error in step *K* cascades
into every subsequent step.

## Notes

* Deterministic. Floats compared with tolerance by the grader.
* Step 1's `--in` is `data/input.json`; step *K*'s `--in` is step *K-1*'s `--out`.
* The `provenance` SHA-256 must be computed from the raw bytes of the file read,
  before JSON parsing.
