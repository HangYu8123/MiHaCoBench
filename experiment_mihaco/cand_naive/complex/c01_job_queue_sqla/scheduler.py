"""Claim/complete/fail logic and dependency checking."""

import json
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from models import Job, Dependency


def get_claimable_job(session: Session) -> Job | None:
    """
    Find the highest-priority claimable job.

    A job is claimable iff:
      - status == "pending"
      - all dependencies have status == "done"

    Tie-breaking:
      1. Higher priority wins.
      2. Among equal priority, lower id wins.
    """
    # Get all pending jobs
    pending_jobs = (
        session.execute(
            select(Job)
            .where(Job.status == "pending")
            .order_by(Job.priority.desc(), Job.id.asc())
        )
        .scalars()
        .all()
    )

    for job in pending_jobs:
        if _dependencies_satisfied(session, job.id):
            return job

    return None


def _dependencies_satisfied(session: Session, job_id: int) -> bool:
    """Return True if all dependencies of job_id are done."""
    deps = (
        session.execute(
            select(Dependency).where(Dependency.job_id == job_id)
        )
        .scalars()
        .all()
    )

    for dep in deps:
        dep_job = session.get(Job, dep.depends_on_id)
        if dep_job is None or dep_job.status != "done":
            return False

    return True


def claim_job(session: Session) -> dict | None:
    """Claim the best claimable job, mark it running, return its dict."""
    job = get_claimable_job(session)
    if job is None:
        return None

    job.status = "running"
    session.flush()

    return {
        "id": job.id,
        "name": job.name,
        "payload": job.get_payload(),
        "priority": job.priority,
    }


def complete_job(session: Session, job_id: int, result: dict | None = None) -> None:
    """Mark job as done and store result."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.status = "done"
    job.set_result(result)
    session.flush()


def fail_job(session: Session, job_id: int, max_retries: int) -> None:
    """
    Record a failure attempt.

    1. Increment attempts by 1.
    2. If new attempts < max_retries: set status back to "pending".
    3. If new attempts >= max_retries: set status to "failed".
    """
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    job.attempts += 1
    if job.attempts < max_retries:
        job.status = "pending"
    else:
        job.status = "failed"
    session.flush()


def get_job_status(session: Session, job_id: int) -> str:
    """Return the current status of job_id."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    return job.status


def get_stats(session: Session) -> dict:
    """Return counts for each status."""
    all_statuses = ["pending", "running", "done", "failed"]
    result = {s: 0 for s in all_statuses}

    rows = session.execute(
        select(Job.status, func.count(Job.id)).group_by(Job.status)
    ).all()

    for status, count in rows:
        result[status] = count

    return result
