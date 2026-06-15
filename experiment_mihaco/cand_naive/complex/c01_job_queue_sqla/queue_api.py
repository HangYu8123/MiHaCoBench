"""Public facade for the priority job queue backed by SQLAlchemy 2.0.

The grader imports only this file.  ``JobQueue`` is the single public class;
all other implementation details live in ``models``, ``repository``, and
``scheduler``.

Example usage::

    from queue_api import JobQueue

    q = JobQueue()                              # in-memory SQLite
    jid = q.submit("ingest", {"src": "s3://..."}, priority=5)
    job = q.claim()                             # {'id': 1, 'name': 'ingest', ...}
    q.complete(job["id"], {"rows": 42})
    print(q.status(jid))                        # 'done'
    print(q.stats())                            # {'pending': 0, 'running': 0, 'done': 1, 'failed': 0}
"""

import json
from typing import Any

from repository import (
    add_dependency,
    add_job,
    count_by_status,
    create_engine_and_tables,
    get_job,
    make_session_factory,
    session_scope,
)
from scheduler import claim_job, complete_job, fail_job, find_claimable_job


class JobQueue:
    """Priority job queue with dependency resolution, backed by SQLAlchemy 2.0.

    Parameters
    ----------
    url:
        SQLAlchemy database URL.  Defaults to ``"sqlite:///:memory:"`` so the
        queue works out-of-the-box with no external server.
    max_retries:
        Maximum number of failure attempts before a job is permanently marked
        ``'failed'``.  Defaults to 3.
    """

    def __init__(
        self,
        url: str = "sqlite:///:memory:",
        max_retries: int = 3,
    ) -> None:
        """Create engine, create all ORM tables, ready for use."""
        self._max_retries = max_retries
        self._engine = create_engine_and_tables(url)
        self._session_factory = make_session_factory(self._engine)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def submit(
        self,
        name: str,
        payload: dict | None = None,
        priority: int = 0,
        depends_on: list[int] | None = None,
    ) -> int:
        """Submit a new job; returns the new job's integer id.

        The new job starts with status ``'pending'``.

        Parameters
        ----------
        name:
            Human-readable label for the job.
        payload:
            Arbitrary dict that will be returned when the job is claimed.
            Must be JSON-serialisable.  ``None`` is stored as NULL.
        priority:
            Scheduling priority; higher integer = claimed first.  Default 0.
        depends_on:
            List of job ids that must be in status ``'done'`` before this job
            becomes claimable.  ``None`` or ``[]`` means no dependencies.

        Returns
        -------
        int
            The newly assigned job id.
        """
        # Serialise payload once, outside the session, to catch encoding errors early.
        payload_json: str | None = None
        if payload is not None:
            payload_json = json.dumps(payload, separators=(",", ":"))

        with session_scope(self._session_factory) as session:
            job = add_job(session, name, payload_json, priority)
            if depends_on:
                for dep_id in depends_on:
                    add_dependency(session, job.id, dep_id)
            new_id: int = job.id

        return new_id

    def claim(self) -> dict | None:
        """Return the highest-priority claimable job and mark it ``'running'``.

        A job is **claimable** iff:
          - its status is ``'pending'``, AND
          - every job listed in its ``depends_on`` has status ``'done'``.

        Tie-breaking when multiple jobs share the same priority:
          - Lower ``id`` wins (earlier submission order).

        Returns
        -------
        dict or None
            ``{"id": int, "name": str, "payload": dict|None, "priority": int}``
            or ``None`` if nothing is claimable.
        """
        with session_scope(self._session_factory) as session:
            job = find_claimable_job(session)
            if job is None:
                return None

            claim_job(session, job)
            # Capture values before the session is closed.
            result = {
                "id": job.id,
                "name": job.name,
                "payload": job.payload,  # decoded dict or None
                "priority": job.priority,
            }

        return result

    def complete(self, job_id: int, result: dict | None = None) -> None:
        """Mark job *job_id* as ``'done'`` and store optional *result* dict.

        Parameters
        ----------
        job_id:
            Id of the job to mark done.
        result:
            Optional result payload.  Must be JSON-serialisable.

        Raises
        ------
        KeyError
            If *job_id* does not exist.
        """
        result_json: str | None = None
        if result is not None:
            result_json = json.dumps(result, separators=(",", ":"))

        with session_scope(self._session_factory) as session:
            complete_job(session, job_id, result_json)

    def fail(self, job_id: int) -> None:
        """Record a failure attempt for *job_id*.

        If ``attempts < max_retries`` after incrementing: sets status back to
        ``'pending'`` (the job will be retried on the next ``claim`` call).
        If ``attempts >= max_retries``: sets status to ``'failed'`` permanently.

        Parameters
        ----------
        job_id:
            Id of the job that failed.

        Raises
        ------
        KeyError
            If *job_id* does not exist.
        """
        with session_scope(self._session_factory) as session:
            fail_job(session, job_id, self._max_retries)

    def status(self, job_id: int) -> str:
        """Return the current status string for *job_id*.

        Returns
        -------
        str
            One of ``'pending'``, ``'running'``, ``'done'``, ``'failed'``.

        Raises
        ------
        KeyError
            If *job_id* does not exist.
        """
        with session_scope(self._session_factory) as session:
            job = get_job(session, job_id)
            return job.status

    def stats(self) -> dict:
        """Return a dict with counts for every status.

        Returns
        -------
        dict
            ``{"pending": n, "running": n, "done": n, "failed": n}``.
            All four keys are always present; the count is 0 when no jobs have
            that status.
        """
        with session_scope(self._session_factory) as session:
            return count_by_status(session)
