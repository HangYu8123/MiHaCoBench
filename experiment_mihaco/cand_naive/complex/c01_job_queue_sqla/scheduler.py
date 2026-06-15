"""Claim, complete, and fail logic for the priority job queue.

This module contains the core scheduling algorithm:
  - find_claimable_job: identify the best claimable job (dependency-aware)
  - claim_job: atomically mark a job as 'running'
  - complete_job: mark a job 'done' and store its result
  - fail_job: record a failure and either retry or permanently fail the job

All public functions receive an open ``Session`` and operate within the caller's
transaction boundary.
"""

from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session

from models import Dependency, Job
from repository import get_job


def find_claimable_job(session: Session) -> Job | None:
    """Return the highest-priority claimable ``Job`` or ``None``.

    A job is **claimable** iff:
      1. Its status is ``'pending'``.
      2. Every job listed in its dependency edges has status ``'done'``.

    Tie-breaking:
      1. Higher ``priority`` wins.
      2. Among ties, lower ``id`` wins (earlier submission).

    The implementation uses a correlated sub-query so that the entire check
    happens in a single SQL round-trip.
    """
    # Alias for the prerequisite job used inside the subquery
    prereq = Job.__table__.alias("prereq")

    # Subquery: does this job have ANY unsatisfied dependency?
    # An unsatisfied dependency is a Dependency row whose prerequisite job is
    # NOT in status 'done'.
    has_unsatisfied = exists().where(
        and_(
            Dependency.job_id == Job.id,
            # join to the prerequisite job and check its status
            Dependency.depends_on_id == prereq.c.id,
            prereq.c.status != "done",
        )
    )

    stmt = (
        select(Job)
        .where(
            Job.status == "pending",
            ~has_unsatisfied,
        )
        .order_by(Job.priority.desc(), Job.id.asc())
        .limit(1)
    )

    return session.scalars(stmt).first()


def claim_job(session: Session, job: Job) -> None:
    """Transition *job* from ``'pending'`` to ``'running'`` in place.

    The caller is responsible for ensuring that *job* is still pending before
    calling this function (no second re-check is performed here).
    """
    job.status = "running"


def complete_job(
    session: Session, job_id: int, result_json: str | None
) -> None:
    """Mark job *job_id* as ``'done'`` and store *result_json* (raw JSON text or NULL).

    Raises ``KeyError`` if *job_id* does not exist.
    """
    job = get_job(session, job_id)
    job.status = "done"
    job._result = result_json


def fail_job(session: Session, job_id: int, max_retries: int) -> None:
    """Record a failure for job *job_id*.

    - Increments ``attempts``.
    - If ``attempts < max_retries`` after increment: sets status back to
      ``'pending'`` so the job will be retried.
    - If ``attempts >= max_retries``: sets status to ``'failed'`` permanently.

    Raises ``KeyError`` if *job_id* does not exist.
    """
    job = get_job(session, job_id)
    job.attempts += 1
    if job.attempts < max_retries:
        job.status = "pending"
    else:
        job.status = "failed"
