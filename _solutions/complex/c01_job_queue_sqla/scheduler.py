"""Scheduling logic for the priority job queue.

Contains the claim/complete/fail operations with dependency checking.
All operations delegate DB access to ``JobRepository``.
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
        """Return the highest-priority claimable job and mark it 'running'.

        A job is claimable iff:
          - status == 'pending', AND
          - every dependency job has status == 'done'.

        Tie-breaking: higher priority first; among equals, lower id first.
        Returns a dict with keys id/name/payload/priority, or None.
        """
        pending = self._repo.list_pending_jobs()
        for job in pending:
            dep_ids = self._repo.get_dependency_ids(job.id)
            if self._all_done(dep_ids):
                # Claim this job: transition to 'running'.
                self._repo.update_status(job.id, "running")
                return {
                    "id": job.id,
                    "name": job.name,
                    "payload": job.payload,
                    "priority": job.priority,
                }
        return None

    def _all_done(self, dep_ids: list[int]) -> bool:
        """Return True if every dependency job is in 'done' status."""
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
