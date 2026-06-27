"""Public facade — the grader imports THIS file only."""

import sys
import os

# Ensure the task directory is on sys.path so sibling modules can be imported
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from models import Job, Dependency
from repository import create_engine, init_db, get_session
from scheduler import claim_job, complete_job, fail_job, get_status, get_stats


class JobQueue:
    def __init__(self, url: str = "sqlite:///:memory:", max_retries: int = 3) -> None:
        """Create engine, create all ORM tables, ready for use."""
        self._engine = create_engine(url)
        self._max_retries = max_retries
        init_db(self._engine)

    def submit(
        self,
        name: str,
        payload: dict | None = None,
        priority: int = 0,
        depends_on: list[int] | None = None,
    ) -> int:
        """Submit a new job; returns the new job's integer id."""
        with get_session(self._engine) as session:
            job = Job(
                name=name,
                payload=payload,
                priority=priority,
                status="pending",
                attempts=0,
                result=None,
            )
            session.add(job)
            session.flush()  # populate job.id before adding dependencies

            if depends_on:
                for dep_id in depends_on:
                    dep = Dependency(job_id=job.id, depends_on_id=dep_id)
                    session.add(dep)

            session.commit()
            return job.id

    def claim(self) -> dict | None:
        """Return the highest-priority claimable job and mark it running."""
        with get_session(self._engine) as session:
            return claim_job(session)

    def complete(self, job_id: int, result: dict | None = None) -> None:
        """Mark job job_id as done and store optional result dict."""
        with get_session(self._engine) as session:
            complete_job(session, job_id, result)

    def fail(self, job_id: int) -> None:
        """Record a failure attempt for job_id."""
        with get_session(self._engine) as session:
            fail_job(session, job_id, self._max_retries)

    def status(self, job_id: int) -> str:
        """Return the current status string for job_id."""
        with get_session(self._engine) as session:
            return get_status(session, job_id)

    def stats(self) -> dict:
        """Return a dict with counts for every status."""
        with get_session(self._engine) as session:
            return get_stats(session)
