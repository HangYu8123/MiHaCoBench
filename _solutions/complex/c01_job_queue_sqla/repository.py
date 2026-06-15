"""Low-level DB access helpers for the job queue.

Provides session management and basic CRUD operations so that
higher-level modules (scheduler.py, queue_api.py) stay focused on logic.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Dependency, Job


class JobRepository:
    """Thin data-access layer around a SQLAlchemy session factory."""

    def __init__(self, url: str = "sqlite:///:memory:") -> None:
        """Create the engine, apply schema, and prepare a session factory."""
        # connect_args: check_same_thread=False is required for SQLite in-memory DBs
        # when accessed from multiple calls (even from a single thread).
        connect_args = {"check_same_thread": False} if "sqlite" in url else {}
        self._engine = create_engine(url, connect_args=connect_args)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Yield a session that auto-commits on success and rolls back on error."""
        sess = self._Session()
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_job(
        self,
        name: str,
        payload: Optional[dict],
        priority: int,
    ) -> int:
        """Insert a new Job row and return its auto-assigned id."""
        job = Job(name=name, priority=priority)
        job.payload = payload
        with self.session() as sess:
            sess.add(job)
            sess.flush()
            job_id = job.id
        return job_id

    def add_dependency(self, job_id: int, depends_on_id: int) -> None:
        """Record that ``job_id`` depends on ``depends_on_id``."""
        dep = Dependency(job_id=job_id, depends_on_id=depends_on_id)
        with self.session() as sess:
            sess.add(dep)

    def update_status(self, job_id: int, status: str) -> None:
        """Set the status field of a job."""
        with self.session() as sess:
            job = sess.get(Job, job_id)
            if job is None:
                raise KeyError(f"Job {job_id} not found")
            job.status = status

    def set_result(self, job_id: int, result: Optional[dict]) -> None:
        """Store the result dict on a job."""
        with self.session() as sess:
            job = sess.get(Job, job_id)
            if job is None:
                raise KeyError(f"Job {job_id} not found")
            job.result = result

    def increment_attempts(self, job_id: int) -> int:
        """Increment the attempts counter and return the new value."""
        with self.session() as sess:
            job = sess.get(Job, job_id)
            if job is None:
                raise KeyError(f"Job {job_id} not found")
            job.attempts += 1
            return job.attempts

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_job(self, job_id: int) -> Optional[Job]:
        """Return the Job with ``job_id``, or None if not found."""
        with self.session() as sess:
            job = sess.get(Job, job_id)
            if job is None:
                return None
            # Detach a snapshot so callers can inspect after session closes.
            sess.expunge(job)
            return job

    def get_status(self, job_id: int) -> str:
        """Return the status string for a job."""
        with self.session() as sess:
            job = sess.get(Job, job_id)
            if job is None:
                raise KeyError(f"Job {job_id} not found")
            return job.status

    def get_attempts(self, job_id: int) -> int:
        """Return the current attempt count for a job."""
        with self.session() as sess:
            job = sess.get(Job, job_id)
            if job is None:
                raise KeyError(f"Job {job_id} not found")
            return job.attempts

    def list_pending_jobs(self) -> list[Job]:
        """Return all jobs with status 'pending', ordered by priority DESC then id ASC."""
        with self.session() as sess:
            stmt = (
                select(Job)
                .where(Job.status == "pending")
                .order_by(Job.priority.desc(), Job.id.asc())
            )
            jobs = sess.scalars(stmt).all()
            for j in jobs:
                sess.expunge(j)
            return list(jobs)

    def get_dependency_ids(self, job_id: int) -> list[int]:
        """Return the list of job ids that ``job_id`` depends on."""
        with self.session() as sess:
            stmt = select(Dependency.depends_on_id).where(Dependency.job_id == job_id)
            return list(sess.scalars(stmt).all())

    def count_by_status(self) -> dict[str, int]:
        """Return ``{"pending": n, "running": n, "done": n, "failed": n}``."""
        all_statuses = ["pending", "running", "done", "failed"]
        counts: dict[str, int] = {s: 0 for s in all_statuses}
        with self.session() as sess:
            for job in sess.scalars(select(Job)).all():
                if job.status in counts:
                    counts[job.status] += 1
        return counts
