"""Claim/complete/fail logic and dependency checking for the job queue."""

import json

from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from models import Job, Dependency


def claim_job(session, max_retries: int = 3):
    """Find and claim the highest-priority claimable pending job.

    A job is claimable iff:
      - status == "pending"
      - ALL of its dependencies have status == "done"
        (zero-dep jobs are always claimable if pending)

    Returns a dict {"id", "name", "payload", "priority"} or None.
    """
    # Alias for the dependency's upstream job (to check its status)
    DepJob = aliased(Job)

    # Subquery: does any not-done dependency exist for this job?
    dep_not_done = (
        select(Dependency.job_id)
        .join(DepJob, Dependency.depends_on_id == DepJob.id)
        .where(
            Dependency.job_id == Job.id,
            DepJob.status != "done",
        )
        .exists()
    )

    stmt = (
        select(Job)
        .where(Job.status == "pending", ~dep_not_done)
        .order_by(Job.priority.desc(), Job.id.asc())
        .limit(1)
    )

    job = session.scalars(stmt).first()
    if job is None:
        return None

    job.status = "running"
    session.flush()

    payload = None
    if job.payload is not None:
        payload = json.loads(job.payload)

    return {
        "id": job.id,
        "name": job.name,
        "payload": payload,
        "priority": job.priority,
    }


def complete_job(session, job_id: int, result=None) -> None:
    """Mark a job as done and store its result."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.status = "done"
    job.result = json.dumps(result) if result is not None else None
    session.flush()


def fail_job(session, job_id: int, max_retries: int = 3) -> None:
    """Record a failure attempt.

    1. Increment attempts.
    2. If new attempts < max_retries  → set status "pending" (retry).
    3. If new attempts >= max_retries → set status "failed" (permanent).
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


def get_status(session, job_id: int) -> str:
    """Return the current status string for a job."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    return job.status


def get_stats(session) -> dict:
    """Return counts for every status; all four keys always present."""
    rows = session.execute(
        select(Job.status, func.count()).group_by(Job.status)
    ).all()
    counts = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    for status, n in rows:
        counts[status] = n
    return counts
