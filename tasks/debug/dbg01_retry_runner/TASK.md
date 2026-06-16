# Debug 01 — `retry_runner`: a job that never gives up

**Created:** 2026-06-15 · **Category:** debug · **Weight:** 2

You are given a **buggy** implementation of a retrying job runner. Find and fix
the defect, then write your corrected solution as `solution.py` (**standard
library only**). Keep the public contract below exactly; do not rename the
function or change its return shape.

## Buggy implementation

```python
def run_with_retries(attempts, max_retries):
    max_attempts = max_retries + 1
    count = 0
    status = "running"
    for outcome in attempts[:max_attempts]:
        count += 1
        if outcome:
            status = "succeeded"
            break
        if count > max_attempts:
            status = "failed"
    return {"status": status, "attempts": count}
```

## Symptom (failing behavior)

A job whose every attempt fails should end in the terminal state `"failed"` once
it has used up its retry budget. Instead it stays stuck in the non-terminal
`"running"` state:

```text
>>> run_with_retries([False, False, False], max_retries=2)
{'status': 'running', 'attempts': 3}   # actual   (wrong)
{'status': 'failed',  'attempts': 3}   # expected
```

Success paths and the `attempts` count are already correct — only the terminal
failure transition is broken.

## Public contract (must match exactly)

```python
def run_with_retries(attempts: list[bool], max_retries: int) -> dict:
    ...
```

* The first try is **attempt 1**. On failure the job is retried for at most
  `max_retries` retries — i.e. at most `max_retries + 1` **total** attempts.
* `attempts[i]` is the outcome of the (i+1)-th attempt (`True` = success).
  Execution stops at the **first** success.
* Return `{"status": ..., "attempts": <count>}` where:
  * `status` is `"succeeded"` if some attempt within the budget returned `True`;
  * `status` is `"failed"` if no attempt succeeds — i.e. the retry budget **or**
    the provided `attempts` outcomes are exhausted first;
  * `attempts` is the number of attempts actually made (capped at the budget and
    at the number of provided outcomes).

## Notes

* Standard library only. Determinism: identical input ⇒ identical output.
