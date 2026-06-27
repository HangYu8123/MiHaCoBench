"""Public facade for the priority job queue backed by SQLAlchemy 2.0 ORM."""

import json

from models import Base, Job, Dependency
from repository import make_engine, make_session_factory
import scheduler as _sched


class JobQueue:
    """Priority job queue with dependency resolution.

    Parameters
    ----------
    url : str
        SQLAlchemy database URL. Defaults to in-memory SQLite.
    max_retries : int
        Maximum total failure attempts before a job is marked "failed".
    """

    def __init__(self, url: str = "sqlite:///:memory:", max_retries: int = 3) -> None:
        self._max_retries = max_retries
        self._engine = make_engine(url)
        Base.metadata.create_all(self._engine)
        factory = make_session_factory(self._engine)
        # Keep a single persistent session for the in-memory SQLite case.
        self._session = factory()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(
        self,
        name: str,
        payload: dict | None = None,
        priority: int = 0,
        depends_on: list[int] | None = None,
    ) -> int:
        """Submit a new job and return its integer id.

        ``depends_on`` may be ``None`` or an empty list (no dependencies).
        """
        job = Job(
            name=name,
            payload=json.dumps(payload) if payload is not None else None,
            priority=priority,
            status="pending",
            attempts=0,
        )
        self._session.add(job)
        self._session.flush()  # populate job.id

        if depends_on:
            for dep_id in depends_on:
                dep = Dependency(job_id=job.id, depends_on_id=dep_id)
                self._session.add(dep)

        self._session.commit()
        return job.id

    def claim(self) -> dict | None:
        """Return and mark running the highest-priority claimable job.

        Returns ``{"id", "name", "payload", "priority"}`` or ``None``.
        """
        result = _sched.claim_job(self._session, self._max_retries)
        self._session.commit()
        return result

    def complete(self, job_id: int, result: dict | None = None) -> None:
        """Mark a job as done and store its optional result."""
        _sched.complete_job(self._session, job_id, result)
        self._session.commit()

    def fail(self, job_id: int) -> None:
        """Record a failure attempt; retry or mark failed per max_retries."""
        _sched.fail_job(self._session, job_id, self._max_retries)
        self._session.commit()

    def status(self, job_id: int) -> str:
        """Return the current status string for job_id."""
        return _sched.get_status(self._session, job_id)

    def stats(self) -> dict:
        """Return ``{"pending": n, "running": n, "done": n, "failed": n}``."""
        return _sched.get_stats(self._session)
