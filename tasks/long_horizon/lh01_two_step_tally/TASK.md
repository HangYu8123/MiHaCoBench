# Long-Horizon 01 — `two_step_tally` (2 steps)

**Created:** 2026-06-15 · **Category:** long_horizon · **Horizon:** 2 steps · **Weight:** 1

Build a **2-step pipeline** as a single file `solution.py`. Each step is run
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

* **Input** (`data/input.json`, given): `{"values": [5, 3, 8, 1, 9, 2, 7]}`.
* **Step 1 — `scale_and_shift`:** read `values`; produce
  `data = [v * 2 + 1 for v in values]`. (Here: `[11, 7, 17, 3, 19, 5, 15]`.)
* **Step 2 — `cumulative_stats`:** read the **list** in step 1's `data`; produce
  ```json
  {"cumsum": [running cumulative sums], "total": <sum>, "mean": <mean>, "count": <len>}
  ```

Because step 2 reads step 1's output, an error in step 1 makes step 2 wrong too —
the chain **cascades**.

## Notes

* Deterministic. Floats compared with tolerance.
* Step 1's `--in` is `data/input.json`; step 2's `--in` is step 1's `--out`.
