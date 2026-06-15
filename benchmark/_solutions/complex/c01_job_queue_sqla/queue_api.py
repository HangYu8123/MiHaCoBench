"""Public facade for the priority job queue (the grader imports this module).

Provides ``JobQueue`` — the only class a consumer needs.
Delegates to ``JobRepository`` (DB access) and ``Scheduler`` (logic).
"""
from __future__ import annotations

from typing import Optional

from repository import JobRepository
from scheduler import Scheduler


class JobQueue:
    """Priority job queue backed by SQLAlchemy 2.0 ORM with dependency resolution.

    Parameters
    ----------
    url:
        SQLAlchemy database URL.  Defaults to ``"sqlite:///:memory:"`` so
        tests run with no external server.
    max_retries:
        Maximum number of times a job can be retried after ``fail()`` before
        it is permanently marked ``"failed"``.
    """

    def __init__(
        self,
        url: str = "sqlite:///:memory:",
        max_retries: int = 3,
    ) -> None:
        self._repo = JobRepository(url=url)
        self._scheduler = Scheduler(self._repo, max_retries=max_retries)

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def submit(
        self,
        name: str,
        payload: Optional[dict] = None,
        priority: int = 0,
        depends_on: Optional[list[int]] = None,
    ) -> int:
        """Submit a new job and return its integer id.

        The job starts with status ``"pending"``.  If ``depends_on`` is
        provided, each id in the list is recorded as a prerequisite.
        """
        job_id = self._repo.add_job(name=name, payload=payload, priority=priority)
        if depends_on:
            for dep_id in depends_on:
                self._repo.add_dependency(job_id, dep_id)
        return job_id

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def claim(self) -> Optional[dict]:
        """Return the highest-priority claimable job dict and mark it running.

        Returns ``{"id", "name", "payload", "priority"}`` or ``None``.
        """
        return self._scheduler.claim()

    def complete(self, job_id: int, result: Optional[dict] = None) -> None:
        """Mark ``job_id`` as ``"done"`` and store optional ``result``."""
        self._scheduler.complete(job_id, result)

    def fail(self, job_id: int) -> None:
        """Record a failure for ``job_id``.

        Retries up to ``max_retries`` times (status back to ``"pending"``);
        afterwards permanently sets status to ``"failed"``.
        """
        self._scheduler.fail(job_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def status(self, job_id: int) -> str:
        """Return the current status string for ``job_id``."""
        return self._repo.get_status(job_id)

    def stats(self) -> dict:
        """Return counts per status: ``{"pending": n, "running": n, "done": n, "failed": n}``."""
        return self._repo.count_by_status()
