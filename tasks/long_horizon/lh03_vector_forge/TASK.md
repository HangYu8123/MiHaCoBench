# Long-Horizon 03 — `vector_forge` (6 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 6 steps · **Weight:** 3

Build a **6-step vector-processing pipeline** as a single file `solution.py`. Each
step is run separately and **consumes only the artifact written by the previous step**
— you may not re-read the original input from a later step.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out` a
JSON object with **exactly** these keys:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path, 'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

## The chain

**Input** (`data/input.json`, committed): `{"values": [7, 2, 9, 4, 1, 8, 3, 6, 5, 10]}`.

| Step | Name | Operation | Reads from input |
|------|------|-----------|-----------------|
| 1 | `parse` | Cast each element of `values` to `float` (identity, no scaling). | `prev["values"]` |
| 2 | `double` | Multiply each element by 2. | `prev["data"]` |
| 3 | `add_const` | Add 3 to each element. | `prev["data"]` |
| 4 | `filter_gt_mean` | Compute the mean of the list; keep only elements **strictly greater than** the mean. | `prev["data"]` |
| 5 | `sort_desc` | Sort the filtered list in **descending** order. | `prev["data"]` |
| 6 | `aggregate` | Compute summary statistics over the sorted list. | `prev["data"]` |

### Step 6 output contract (`data` key)

```json
{
  "sum":   <float — sum of elements>,
  "mean":  <float — arithmetic mean (sum / count)>,
  "min":   <float — minimum element>,
  "max":   <float — maximum element>,
  "count": <int   — number of elements>
}
```

## Expected chain (for your reference)

- Step 1: `[7.0, 2.0, 9.0, 4.0, 1.0, 8.0, 3.0, 6.0, 5.0, 10.0]`
- Step 2: `[14.0, 4.0, 18.0, 8.0, 2.0, 16.0, 6.0, 12.0, 10.0, 20.0]`
- Step 3: `[17.0, 7.0, 21.0, 11.0, 5.0, 19.0, 9.0, 15.0, 13.0, 23.0]`
- Step 4 (mean=14.0, keep > 14): `[17.0, 21.0, 19.0, 15.0, 23.0]`
- Step 5 (sort desc): `[23.0, 21.0, 19.0, 17.0, 15.0]`
- Step 6: `{"sum": 95.0, "mean": 19.0, "min": 15.0, "max": 23.0, "count": 5}`

## Notes

- Stdlib only — no third-party packages required.
- Deterministic: no randomness. Floats compared with tolerance.
- Step 1's `--in` is `data/input.json`; each later step's `--in` is the previous step's `--out`.
- Because each step reads only the previous artifact, an error in step *K* cascades into all later steps.
