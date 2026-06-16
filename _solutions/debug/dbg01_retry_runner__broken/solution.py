"""Deliberately-broken reference for debug/dbg01_retry_runner.

Planted defect (mirrors the real c01_job_queue retry failure): the terminal
``"failed"`` transition is guarded by ``count > max_attempts``, which can never
be true inside a loop bounded by ``max_attempts``. A job that exhausts its retry
budget therefore stays in the non-terminal ``"running"`` state instead of
becoming ``"failed"``. Success cases and the attempt count remain correct, so the
defect is localized — the grader must catch the missing state transition.
"""
from __future__ import annotations


def run_with_retries(attempts: list[bool], max_retries: int) -> dict:
    max_attempts = max_retries + 1
    count = 0
    status = "running"
    for outcome in attempts[:max_attempts]:
        count += 1
        if outcome:
            status = "succeeded"
            break
        if count > max_attempts:  # off-by-one: never true → "failed" never set
            status = "failed"
    return {"status": status, "attempts": count}
