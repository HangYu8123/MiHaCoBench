# Long-Horizon 05 — `signal_chain` (10 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 10 steps · **Weight:** 5

Build a **10-step signal processing pipeline** as a single file `solution.py`.
Each step is run separately as a CLI command and **consumes only the artifact
written by the previous step** — you may not re-read the original input from
a later step.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out`
a JSON object with **exactly** these keys:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path, 'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

## Input

Committed at `data/input.json`:

```json
{"values": [3.0, 1.0, 4.0, 1.5, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0]}
```

## The chain

| Step | Name | Input | Operation | Output type |
|------|------|-------|-----------|-------------|
| 1 | `parse_float` | `values` list from `input.json` | Cast each element to `float` | `list[float]` (len 12) |
| 2 | `normalize_minmax` | step 1 `data` list | `(v - min) / (max - min)` per element; if `max == min` emit all zeros | `list[float]` (len 12) |
| 3 | `scale` | step 2 `data` list | Multiply each element by `100` | `list[float]` (len 12) |
| 4 | `round3` | step 3 `data` list | Round each element to 3 decimal places (Python `round(v, 3)`) | `list[float]` (len 12) |
| 5 | `moving_avg_3` | step 4 `data` list | Sliding window mean of width 3: result[i] = (data[i] + data[i+1] + data[i+2]) / 3 for i in 0..len-3 | `list[float]` (len 10) |
| 6 | `square` | step 5 `data` list | Square each element: `v * v` | `list[float]` (len 10) |
| 7 | `prefix_max` | step 6 `data` list | Running maximum: result[i] = max(data[0..i]) | `list[float]` (len 10) |
| 8 | `diffs` | step 7 `data` list | Consecutive differences: result[i] = data[i+1] - data[i] for i in 0..len-2 | `list[float]` (len 9) |
| 9 | `sort_desc` | step 8 `data` list | Sort descending | `list[float]` (len 9) |
| 10 | `aggregate` | step 9 `data` list | Summary stats dict | `dict` |

### Step 10 aggregate output format

```json
{"sum": <float>, "mean": <float>, "min": <float>, "max": <float>, "count": <int>}
```

## Notes

* Each step's `--in` is the previous step's `--out`. Step 1's `--in` is `data/input.json`.
* Steps 2+ read the full JSON artifact from the previous step; the list/dict result is under the `"data"` key.
* For step 1, the input file has a `"values"` key directly (not `"data"`).
* Deterministic. Floats compared with tolerance by the grader.
* Error in any step cascades: the grader feeds the candidate's own output forward.
