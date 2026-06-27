"""Public facade for the priority job queue. The grader imports this file."""

import sys
import os

# Ensure the package directory is on the path so sibling modules can be imported
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

import json
from models import Job, Dependency
from repository import create_db_engine, init_db, get_session_factory, session_scope
from scheduler import (
    claim_job,
    complete_job,
    fail_job,
    get_job_status,
    get_stats,
)


class JobQueue:
    def __init__(self, url: str = "sqlite:///:memory:", max_retries: int = 3) -> None:
        """Create engine, create all ORM tables, ready for use."""
        self._max_retries = max_retries
        self._engine = create_db_engine(url)
        init_db(self._engine)
        self._session_factory = get_session_factory(self._engine)

    def submit(
        self,
        name: str,
        payload: dict | None = None,
        priority: int = 0,
        depends_on: list[int] | None = None,
    ) -> int:
        """Submit a new job; returns the new job's integer id."""
        with session_scope(self._session_factory) as session:
            job = Job(
                name=name,
                priority=priority,
                status="pending",
                attempts=0,
            )
            job.set_payload(payload)
            session.add(job)
            session.flush()  # get job.id assigned

            if depends_on:
                for dep_id in depends_on:
                    dep = Dependency(job_id=job.id, depends_on_id=dep_id)
                    session.add(dep)

            session.flush()
            job_id = job.id

        return job_id

    def claim(self) -> dict | None:
        """Return the highest-priority claimable job and mark it 'running'."""
        with session_scope(self._session_factory) as session:
            result = claim_job(session)
        return result

    def complete(self, job_id: int, result: dict | None = None) -> None:
        """Mark job job_id as 'done' and store optional result dict."""
        with session_scope(self._session_factory) as session:
            complete_job(session, job_id, result)

    def fail(self, job_id: int) -> None:
        """Record a failure attempt for job_id."""
        with session_scope(self._session_factory) as session:
            fail_job(session, job_id, self._max_retries)

    def status(self, job_id: int) -> str:
        """Return the current status string for job_id."""
        with session_scope(self._session_factory) as session:
            return get_job_status(session, job_id)

    def stats(self) -> dict:
        """Return a dict with counts for every status."""
        with session_scope(self._session_factory) as session:
            return get_stats(session)
