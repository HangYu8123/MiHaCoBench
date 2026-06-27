"""Claim/complete/fail/status/stats logic using ORM queries."""

import sys
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models import Job, Dependency


def claim_job(session: Session) -> dict | None:
    """
    Find and return the highest-priority claimable pending job, marking it running.

    A job is claimable iff:
      - status == "pending"
      - ALL jobs it depends on have status == "done"
        (equivalently: there is NO dependency row pointing to a non-done job)
    """
    # Subquery: select job_ids that have at least one dependency whose depended-on
    # job is NOT done (i.e., blocked jobs).
    blocked_subq = (
        select(Dependency.job_id)
        .join(Job, Job.id == Dependency.depends_on_id)
        .where(Job.status != "done")
    )

    stmt = (
        select(Job)
        .where(
            Job.status == "pending",
            ~Job.id.in_(blocked_subq),
        )
        .order_by(Job.priority.desc(), Job.id.asc())
        .limit(1)
    )

    job = session.scalars(stmt).first()
    if job is None:
        return None

    # Atomically mark as running within the same session
    job.status = "running"
    session.commit()

    return {
        "id": job.id,
        "name": job.name,
        "payload": job.payload,
        "priority": job.priority,
    }


def complete_job(session: Session, job_id: int, result: dict | None = None) -> None:
    """Mark job as done and store optional result."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.status = "done"
    job.result = result
    session.commit()


def fail_job(session: Session, job_id: int, max_retries: int) -> None:
    """
    Record a failure attempt.

    1. Increment attempts first.
    2. If new attempts < max_retries: set status to "pending" (retry).
    3. If new attempts >= max_retries: set status to "failed" (permanent).
    """
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.attempts += 1
    if job.attempts < max_retries:
        job.status = "pending"
    else:
        job.status = "failed"
    session.commit()


def get_status(session: Session, job_id: int) -> str:
    """Return the current status string for job_id."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    return job.status


def get_stats(session: Session) -> dict:
    """Return counts for all four statuses."""
    rows = session.execute(
        select(Job.status, func.count()).group_by(Job.status)
    ).all()
    result = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    for status, count in rows:
        result[status] = count
    return result
