"""Scheduling logic for the priority job queue (BROKEN variant).

Planted defect: claim() does NOT check dependencies — it returns any pending
job regardless of whether its prerequisites are done. This causes
dependency-order tests to fail.
"""
from __future__ import annotations

from typing import Optional

from repository import JobRepository


class Scheduler:
    """Encapsulates claim/complete/fail logic for the job queue."""

    def __init__(self, repo: JobRepository, max_retries: int = 3) -> None:
        self._repo = repo
        self._max_retries = max_retries

    def claim(self) -> Optional[dict]:
        """Return the highest-priority pending job and mark it 'running'.

        BUG: dependency check omitted — jobs are claimable even if their
        prerequisites have not finished yet.
        """
        pending = self._repo.list_pending_jobs()
        for job in pending:
            # DEFECT: we do NOT call _all_done(); dependencies are ignored.
            self._repo.update_status(job.id, "running")
            return {
                "id": job.id,
                "name": job.name,
                "payload": job.payload,
                "priority": job.priority,
            }
        return None

    def _all_done(self, dep_ids: list[int]) -> bool:
        """(Unused in the broken variant.) Check if all deps are done."""
        for dep_id in dep_ids:
            if self._repo.get_status(dep_id) != "done":
                return False
        return True

    def complete(self, job_id: int, result: Optional[dict] = None) -> None:
        """Mark ``job_id`` as 'done' and store optional result."""
        self._repo.set_result(job_id, result)
        self._repo.update_status(job_id, "done")

    def fail(self, job_id: int) -> None:
        """Record a failure: retry if under max_retries, else mark 'failed'."""
        new_attempts = self._repo.increment_attempts(job_id)
        if new_attempts < self._max_retries:
            self._repo.update_status(job_id, "pending")
        else:
            self._repo.update_status(job_id, "failed")
