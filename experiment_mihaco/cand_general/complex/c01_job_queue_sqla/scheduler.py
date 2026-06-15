"""Claim / complete / fail logic and dependency-aware scheduling.

All functions accept a live ``Session`` as their first argument.  The caller
(``queue_api.py``) is responsible for opening the session, committing or
rolling back, and closing it.

Dependency resolution
---------------------
A job is **claimable** iff:

1. Its ``status`` is ``'pending'``.
2. There is **no** row in ``dependencies`` where
   ``dependency.job_id == job.id`` AND the corresponding
   ``jobs.status != 'done'``.

Condition 2 is expressed as a correlated ``NOT EXISTS`` subquery so that
jobs with zero dependencies are always considered claimable (``NOT EXISTS``
over an empty set is ``True``).

Note on deleted prerequisite jobs
----------------------------------
If a ``depends_on_id`` references a job that no longer exists in the
``jobs`` table, the inner JOIN produces no row for that dependency row,
so ``NOT EXISTS`` evaluates to ``True`` for it.  The job therefore becomes
claimable.  The spec does not address this edge case; the behaviour here
matches "orphaned dependency = satisfied dependency".
"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from models import Dependency, Job

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_job(session: Session, job_id: int) -> Job:
    """Return the :class:`Job` with *job_id*, raising ``KeyError`` if absent."""
    job = session.get(Job, job_id)
    if job is None:
        raise KeyError(f"No job with id={job_id!r}")
    return job


def _decode_payload(raw: Optional[str]) -> Optional[dict]:
    """Decode a JSON-serialised payload/result column value.

    Returns ``None`` when *raw* is SQL NULL (i.e. Python ``None``).
    """
    if raw is None:
        return None
    return json.loads(raw)  # type: ignore[return-value]


def _encode_payload(value: Optional[dict]) -> Optional[str]:
    """Encode a dict as a JSON string, or return ``None`` for SQL NULL."""
    if value is None:
        return None
    return json.dumps(value)


# ---------------------------------------------------------------------------
# Claimability subquery
# ---------------------------------------------------------------------------


def _unfinished_dep_exists(outer_job_alias) -> object:
    """Return a correlated EXISTS subquery for 'has unfinished dependencies'.

    The subquery selects ``1`` from ``dependencies`` joined to ``jobs``
    (the prerequisite side) where:

    * ``dependencies.job_id`` matches the outer job's ``id``, AND
    * the prerequisite job's ``status`` is NOT ``'done'``.

    Using ``NOT EXISTS(...)`` over this subquery makes a pending job
    claimable only when every prerequisite is done.
    """
    # Alias the Job table for the prerequisite side of the join to avoid
    # ambiguity with the outer Job reference.
    from sqlalchemy.orm import aliased

    prereq = aliased(Job, name="prereq")

    subq = (
        select(literal(1))
        .select_from(Dependency)
        .join(prereq, prereq.id == Dependency.depends_on_id)
        .where(
            Dependency.job_id == outer_job_alias.id,
            prereq.status != "done",
        )
        .exists()
    )
    return subq


# ---------------------------------------------------------------------------
# Public scheduler functions
# ---------------------------------------------------------------------------


def claim_job(session: Session) -> Optional[dict]:
    """Find and claim the highest-priority claimable pending job.

    Selects the ``'pending'`` job that has **no unfinished dependencies**,
    orders by ``priority DESC, id ASC``, and takes the first row.

    The selected job's ``status`` is immediately set to ``'running'`` and the
    change is flushed within the caller's transaction.

    Parameters
    ----------
    session:
        An open ``Session`` with an active transaction.

    Returns
    -------
    dict or None
        ``{"id": int, "name": str, "payload": dict|None, "priority": int}``
        if a claimable job exists, otherwise ``None``.
    """
    # Build a correlated NOT EXISTS for unfinished dependencies.
    unfinished_dep = _unfinished_dep_exists(Job)

    stmt = (
        select(Job)
        .where(
            Job.status == "pending",
            ~unfinished_dep,  # bitwise NOT on Exists object
        )
        .order_by(Job.priority.desc(), Job.id.asc())
        .limit(1)
    )

    job: Optional[Job] = session.scalars(stmt).first()
    if job is None:
        return None

    # Transition to running inside the same transaction.
    job.status = "running"
    session.flush()

    return {
        "id": job.id,
        "name": job.name,
        "payload": _decode_payload(job.payload),
        "priority": job.priority,
    }


def complete_job(
    session: Session,
    job_id: int,
    result: Optional[dict],
) -> None:
    """Mark *job_id* as ``'done'`` and persist an optional *result* dict.

    Parameters
    ----------
    session:
        An open ``Session`` with an active transaction.
    job_id:
        Integer primary key of the job to complete.
    result:
        Optional dict to store.  ``None`` stores SQL NULL.

    Raises
    ------
    KeyError
        If no job with *job_id* exists.
    """
    job = _load_job(session, job_id)
    job.status = "done"
    job.result = _encode_payload(result)


def fail_job(
    session: Session,
    job_id: int,
    max_retries: int,
) -> None:
    """Record a failure attempt for *job_id*.

    The check is performed on the **current** value of ``attempts`` *before*
    any mutation, exactly as the spec states:

    * If ``attempts < max_retries``: increment ``attempts`` by 1, then
      set ``status`` back to ``'pending'`` so the job will be retried.
    * If ``attempts >= max_retries``: set ``status`` to ``'failed'``
      (permanent failure; ``attempts`` is NOT incremented).

    Boundary example with ``max_retries=3``:

    +--------+-------------------+------------------+------------------+
    | Call # | attempts (before) | Condition        | Effect           |
    +========+===================+==================+==================+
    | 1      | 0                 | 0 < 3 → retry    | attempts=1, pend |
    | 2      | 1                 | 1 < 3 → retry    | attempts=2, pend |
    | 3      | 2                 | 2 < 3 → retry    | attempts=3, pend |
    | 4      | 3                 | 3 >= 3 → fail    | failed           |
    +--------+-------------------+------------------+------------------+

    Parameters
    ----------
    session:
        An open ``Session`` with an active transaction.
    job_id:
        Integer primary key of the job that failed.
    max_retries:
        Maximum number of retry attempts permitted.

    Raises
    ------
    KeyError
        If no job with *job_id* exists.
    """
    job = _load_job(session, job_id)
    # Pre-increment check: use the CURRENT value of attempts.
    if job.attempts < max_retries:
        job.attempts += 1
        job.status = "pending"
    else:
        job.status = "failed"


def get_status(session: Session, job_id: int) -> str:
    """Return the current status string for *job_id*.

    Parameters
    ----------
    session:
        An open ``Session``.
    job_id:
        Integer primary key of the job to query.

    Returns
    -------
    str
        One of ``'pending'``, ``'running'``, ``'done'``, ``'failed'``.

    Raises
    ------
    KeyError
        If no job with *job_id* exists.
    """
    job = _load_job(session, job_id)
    return str(job.status)


def get_stats(session: Session) -> dict:
    """Return a dict with counts for every status.

    All four status keys are always present; missing statuses get a count
    of 0.

    Parameters
    ----------
    session:
        An open ``Session``.

    Returns
    -------
    dict
        ``{"pending": int, "running": int, "done": int, "failed": int}``.
    """
    # Start with baseline so all four keys are always present.
    result: dict[str, int] = {"pending": 0, "running": 0, "done": 0, "failed": 0}

    rows = session.execute(
        select(Job.status, func.count()).group_by(Job.status)
    ).all()

    for status, count in rows:
        result[str(status)] = int(count)

    return result
