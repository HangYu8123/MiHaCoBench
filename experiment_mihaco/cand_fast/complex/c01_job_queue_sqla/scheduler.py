"""Core scheduling logic: claim, complete, and fail operations.

All functions accept an open SQLAlchemy :class:`Session` and operate within
the caller's transaction — the caller is responsible for commit/rollback.

Dependency resolution
---------------------
A job is *claimable* iff:
  1. Its status is ``"pending"``.
  2. Every dependency listed in the ``Dependency`` table for that job has
     status ``"done"`` in the ``Job`` table.

Tie-breaking order for ``claim_job``:
  1. Highest ``priority`` first (larger int wins).
  2. Lowest ``id`` first among equal-priority jobs (earlier submission wins).
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Dependency, Job

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_STATUSES = ("pending", "running", "done", "failed")


def _claimable_stmt():
    """Return a SELECT statement that matches claimable pending jobs.

    A job is claimable when no *unfinished* dependency exists, i.e.
    there is no row in ``Dependency`` for that job whose referenced
    ``depends_on_id`` has status != ``"done"``.

    Uses NOT EXISTS with a correlated subquery for correctness:
    - Jobs with *no* dependency rows are immediately claimable.
    - Jobs with dependency rows are claimable only when ALL referenced jobs
      are ``"done"``.
    """
    # Alias the dependency table to a correlated alias so SQLAlchemy can
    # differentiate the inner Job from the outer Job.
    dep_job = Job.__table__.alias("dep_job")

    # Correlated subquery: select 1 where there exists an unfinished dep.
    unfinished_dep = (
        select(Dependency.depends_on_id)
        .where(Dependency.job_id == Job.id)          # correlated on outer job.id
        .join(dep_job, dep_job.c.id == Dependency.depends_on_id)
        .where(dep_job.c.status != "done")
        .correlate(Job)                              # explicit correlation
    )

    stmt = (
        select(Job)
        .where(Job.status == "pending")
        .where(~unfinished_dep.exists())             # NOT EXISTS
        .order_by(Job.priority.desc(), Job.id.asc())
        .limit(1)
    )
    return stmt


# ---------------------------------------------------------------------------
# Public scheduling functions
# ---------------------------------------------------------------------------


def claim_job(session: Session) -> Job | None:
    """Find and atomically mark the highest-priority claimable job as ``"running"``.

    Parameters
    ----------
    session:
        An active SQLAlchemy session (transaction already open).

    Returns
    -------
    Job or None
        The claimed :class:`Job` ORM object, or ``None`` if nothing is
        currently claimable.
    """
    stmt = _claimable_stmt()
    job = session.scalar(stmt)
    if job is None:
        return None
    job.status = "running"
    session.flush()  # write to DB within the transaction before commit
    return job


def complete_job(session: Session, job_id: int, result: dict | None = None) -> None:
    """Mark *job_id* as ``"done"`` and optionally store *result*.

    Parameters
    ----------
    session:
        An active SQLAlchemy session.
    job_id:
        Primary key of the job to complete.
    result:
        Optional result payload to persist.

    Raises
    ------
    ValueError
        If no job with *job_id* exists.
    """
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"No job with id={job_id!r}")
    job.status = "done"
    job.result = result
    session.flush()


def fail_job(session: Session, job_id: int, max_retries: int) -> None:
    """Record a failure attempt for *job_id*.

    The retry logic follows the spec exactly:

    - If ``job.attempts < max_retries``: increment ``attempts``, reset
      status to ``"pending"`` so the scheduler will retry the job.
    - If ``job.attempts >= max_retries``: set status to ``"failed"``
      permanently (``attempts`` is still incremented for auditability).

    Parameters
    ----------
    session:
        An active SQLAlchemy session.
    job_id:
        Primary key of the job that failed.
    max_retries:
        Maximum number of attempts allowed before permanent failure.

    Raises
    ------
    ValueError
        If no job with *job_id* exists.
    """
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"No job with id={job_id!r}")
    if job.attempts < max_retries:
        job.attempts += 1
        job.status = "pending"
    else:
        # attempts >= max_retries: permanently failed
        job.attempts += 1
        job.status = "failed"
    session.flush()


def get_stats(session: Session) -> dict:
    """Return per-status job counts; all four status keys are always present.

    Parameters
    ----------
    session:
        An active SQLAlchemy session.

    Returns
    -------
    dict
        ``{"pending": int, "running": int, "done": int, "failed": int}``
    """
    rows = session.execute(
        select(Job.status, func.count(Job.id)).group_by(Job.status)
    ).all()
    counts: dict[str, int] = {s: 0 for s in _STATUSES}
    for status, cnt in rows:
        if status in counts:
            counts[status] = cnt
    return counts
