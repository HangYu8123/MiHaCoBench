# Long-Horizon 06 — `matrix_ladder` (12 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 12 steps · **Weight:** 6

Build a **12-step pipeline** as a single file `solution.py`. Each step is run
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

`provenance` is `hashlib.sha256(open(in_path, 'rb').read()).hexdigest()`. The
grader verifies this field, so step *K* must genuinely read and hash the file
produced by step *K-1*.

## The chain

**Input** (`data/input.json`, committed):
```json
{"values": [5, 12, 7, 3, 19, 8, 14, 2, 11, 6, 17, 9, 4, 13, 1, 16]}
```

| Step | Name | Operation | Input key | Output |
|------|------|-----------|-----------|--------|
| 1 | `parse` | Convert each integer in `values` to `float` | `"values"` (list of ints) | `list[float]` |
| 2 | `add_const` | Add `5.0` to every element | step 1 `"data"` | `list[float]` |
| 3 | `mod` | Apply `% 7` to every element (Python float `%`) | step 2 `"data"` | `list[float]` |
| 4 | `scale_by_index` | Multiply element at position `i` by `i` (**0-based**) | step 3 `"data"` | `list[float]` |
| 5 | `cumsum` | Running cumulative sum left-to-right | step 4 `"data"` | `list[float]` (same length) |
| 6 | `prefix_max` | Running maximum left-to-right | step 5 `"data"` | `list[float]` (same length) |
| 7 | `diffs` | Consecutive differences: `data[i+1] - data[i]` | step 6 `"data"` | `list[float]` (length n-1) |
| 8 | `abs` | Absolute value of every element | step 7 `"data"` | `list[float]` |
| 9 | `filter_gt_mean` | Keep only elements **strictly greater than** the mean of the list | step 8 `"data"` | `list[float]` (subset, original order) |
| 10 | `sort_asc` | Sort elements ascending | step 9 `"data"` | `list[float]` |
| 11 | `dedupe` | Remove duplicate values, **preserving order** of first occurrence | step 10 `"data"` | `list[float]` |
| 12 | `aggregate` | Compute summary statistics | step 11 `"data"` | `dict` (see below) |

### Step 12 output format

```json
{
  "total": <sum of all elements, float>,
  "mean":  <arithmetic mean, float>,
  "count": <number of elements, int>,
  "min":   <minimum value, float>,
  "max":   <maximum value, float>
}
```

## Error cascade

Step *K* reads the artifact written by step *K-1*. A wrong step *K-1* will
yield a wrong step *K*. The grader feeds each step's own output forward.

## Notes

* All numeric results are `float` except `count` in step 12 which is `int`.
* Use Python's built-in `%` operator for step 3 — same as `math.fmod` for
  non-negative floats.
* Step 4 index is **0-based**: element at position 0 is multiplied by 0, element
  at position 1 by 1, etc.
* Deterministic — no randomness.
* Use only the Python standard library (`json`, `hashlib`, `argparse`, `math`,
  `itertools`, etc.).
