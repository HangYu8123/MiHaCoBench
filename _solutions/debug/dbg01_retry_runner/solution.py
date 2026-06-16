"""Gold reference for debug/dbg01_retry_runner — a retrying job runner (stdlib only).

The original code never transitioned an exhausted job to ``"failed"`` (an
off-by-one in the retry budget left it stuck in the non-terminal ``"running"``
state). The fix tracks the attempt budget correctly so a job that uses up all of
its allowed attempts without a success ends as ``"failed"``.
"""
from __future__ import annotations


def run_with_retries(attempts: list[bool], max_retries: int) -> dict:
    """Run a job that may fail, retrying up to ``max_retries`` times.

    The first try is attempt 1; on failure the job is retried, for at most
    ``max_retries`` retries — i.e. at most ``max_retries + 1`` total attempts.
    ``attempts[i]`` is the outcome of the (i+1)-th attempt (``True`` = success).
    Execution stops at the first success.

    Returns ``{"status": "succeeded" | "failed", "attempts": <count>}``:
    * ``"succeeded"`` if some attempt within the budget returned ``True``;
    * ``"failed"`` if the whole budget is consumed with no success.
    """
    max_attempts = max_retries + 1
    count = 0
    for outcome in attempts[:max_attempts]:
        count += 1
        if outcome:
            return {"status": "succeeded", "attempts": count}
    return {"status": "failed", "attempts": count}
