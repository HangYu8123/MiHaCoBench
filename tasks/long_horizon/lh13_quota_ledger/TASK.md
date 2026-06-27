# Long-Horizon 13 — `quota_ledger` (10 steps, global budget invariant)

**Created:** 2026-06-17 · **Category:** long_horizon · **Horizon:** 10 steps · **Weight:** 5

Build a **10-step budget-allocation ledger** as a single file `solution.py`. Each
step is run separately as a CLI command and **consumes only the artifact written
by the previous step** — you may not re-read the original input from a later step.

Unlike a stateless transform chain, this pipeline threads a **global invariant**:
a fixed budget set at step 1 is drawn down as requests are granted. The running
remainder set by step *K-1* is the only correct basis for step *K*'s decision —
re-deriving anything from the full budget silently overdraws.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out`:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path, 'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

## Input

Committed at `data/input.json`:

```json
{"budget": 100, "requests": [{"id": "r1", "amount": 30}, ...]}
```

There are **8 requests**, processed strictly in the given (FIFO) order — exactly
one request per processing step (steps 2 through 9).

## The chain

| Step | Name | Reads | Operation | `data` output |
|------|------|-------|-----------|---------------|
| 1 | `init` | `input.json` | Load the budget and queue; commit nothing yet | `{"budget", "remaining"=budget, "queue"=[8 requests], "committed"=[]}` |
| 2–9 | `grant_next` | step *K-1* `data` | Pop the **front** request; grant `g = min(amount, remaining)` against the **running** `remaining`; decrement `remaining` by `g`; append a commitment | `{"budget", "remaining", "queue"=rest, "committed"=[…, {"id","requested","granted"}]}` |
| 10 | `reconcile` | step 9 `data` | Summarise the ledger and check conservation | summary dict (below) |

Each request `{"id", "amount"}` becomes a commitment `{"id", "requested": amount,
"granted": g}` where `g = min(amount, remaining_at_that_step)`. A request may be
**fully granted** (`g == amount`), **partially granted** (`0 < g < amount`, when the
remaining budget runs short), or **rejected** (`g == 0`, when nothing remains).

### Step 10 reconcile output format

```json
{
  "budget": <float>,
  "total_granted": <float>,        // sum of all granted amounts
  "remaining": <float>,            // budget left after all grants
  "utilization": <float>,          // total_granted / budget
  "fully_granted": <int>,
  "partial": <int>,
  "rejected": <int>,
  "reconciled": <bool>             // true iff total_granted + remaining == budget
}
```

## Notes

* Steps 2+ read the previous step's full JSON artifact; the state is under `"data"`.
  Step 1 reads `input.json`, which has `"budget"` and `"requests"` keys directly.
* **Carry the running `remaining` and the `committed` list forward every step.**
  Deriving the grant from the full budget instead of the running remainder
  overdraws and breaks reconciliation.
* Deterministic; floats compared with tolerance by the grader.
* Error in any step cascades: the grader feeds the candidate's own output forward.
