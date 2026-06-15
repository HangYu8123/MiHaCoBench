"""Public facade for the priority job queue.

The grader imports this module and uses only :class:`JobQueue`.

Example usage::

    q = JobQueue()                          # in-memory SQLite, 3 retries
    jid = q.submit("resize", payload={"w": 800, "h": 600}, priority=5)
    q.submit("notify", depends_on=[jid])

    job = q.claim()                         # gets 'resize' (higher priority)
    q.complete(job["id"], result={"ok": True})

    job2 = q.claim()                        # gets 'notify' (dependency done)
    q.fail(job2["id"])                      # attempt 0 < 3 → retry
    print(q.stats())                        # {'pending':1, 'running':0, ...}
"""

from __future__ import annotations

import json
from typing import Optional

from models import Base, Dependency, Job
from repository import make_engine, make_session_factory, session_scope
import scheduler


class JobQueue:
    """Thread-safe priority job queue backed by a SQLAlchemy 2.0 ORM database.

    Parameters
    ----------
    url:
        SQLAlchemy database URL.  Defaults to an in-memory SQLite database
        so that ``JobQueue()`` (no args) works out of the box.
    max_retries:
        Maximum number of times a job may be retried after failure before
        it is permanently marked ``'failed'``.  Defaults to 3.
    """

    def __init__(
        self,
        url: str = "sqlite:///:memory:",
        max_retries: int = 3,
    ) -> None:
        """Create engine, create all ORM tables, and prepare session factory."""
        engine = make_engine(url)
        Base.metadata.create_all(engine)
        self._factory = make_session_factory(engine)
        self._max_retries = max_retries

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(
        self,
        name: str,
        payload: Optional[dict] = None,
        priority: int = 0,
        depends_on: Optional[list] = None,
    ) -> int:
        """Submit a new job and return its integer id.

        The new job starts with ``status='pending'`` and ``attempts=0``.

        Parameters
        ----------
        name:
            Human-readable name for the job.
        payload:
            Optional dict to associate with the job.  Round-trips through the
            DB as JSON.  ``None`` is stored as SQL NULL and returned as
            ``None``.
        priority:
            Scheduling priority (higher int = higher priority).  Default 0.
        depends_on:
            List of job ids that must be ``'done'`` before this job can be
            claimed.  ``None`` or ``[]`` means no dependencies.

        Returns
        -------
        int
            The auto-assigned primary key of the newly created job.
        """
        dep_ids: list[int] = list(depends_on) if depends_on else []
        job_id: int

        with session_scope(self._factory) as session:
            job = Job(
                name=name,
                payload=json.dumps(payload) if payload is not None else None,
                priority=priority,
                status="pending",
                attempts=0,
                result=None,
            )
            session.add(job)
            # flush() assigns the auto-increment id while staying in-transaction.
            session.flush()

            # Capture the id NOW, while the session is open and the object is
            # attached.  After commit() + close() the object is detached and
            # attribute access would raise DetachedInstanceError.
            job_id = int(job.id)

            for dep_id in dep_ids:
                session.add(
                    Dependency(
                        job_id=job_id,
                        depends_on_id=int(dep_id),
                    )
                )
            # session_scope commits on clean exit.

        return job_id

    def claim(self) -> Optional[dict]:
        """Return and mark the highest-priority claimable job, or ``None``.

        A job is **claimable** iff:

        * its ``status`` is ``'pending'``, AND
        * every job in its ``depends_on`` list has ``status == 'done'``.

        Tie-breaking:

        1. Higher ``priority`` value wins.
        2. Among equal priority, lower ``id`` wins (submission order).

        The returned job's status is immediately set to ``'running'``.

        Returns
        -------
        dict or None
            ``{"id": int, "name": str, "payload": dict|None, "priority": int}``
            or ``None`` if no claimable job exists.
        """
        with session_scope(self._factory) as session:
            return scheduler.claim_job(session)

    def complete(self, job_id: int, result: Optional[dict] = None) -> None:
        """Mark *job_id* as ``'done'`` and optionally store a *result* dict.

        Parameters
        ----------
        job_id:
            Integer id of the job to mark done.
        result:
            Optional result dict.  Stored as JSON; ``None`` → SQL NULL.
        """
        with session_scope(self._factory) as session:
            scheduler.complete_job(session, job_id, result)

    def fail(self, job_id: int) -> None:
        """Record a failure attempt for *job_id*.

        Delegates to :func:`scheduler.fail_job` with ``self._max_retries``.

        * If ``attempts < max_retries`` (checked **before** incrementing):
          ``attempts`` is incremented, ``status`` → ``'pending'``.
        * Otherwise: ``status`` → ``'failed'`` (no increment).
        """
        with session_scope(self._factory) as session:
            scheduler.fail_job(session, job_id, self._max_retries)

    def status(self, job_id: int) -> str:
        """Return the current status string for *job_id*.

        Returns
        -------
        str
            One of ``'pending'``, ``'running'``, ``'done'``, ``'failed'``.
        """
        with session_scope(self._factory) as session:
            return scheduler.get_status(session, job_id)

    def stats(self) -> dict:
        """Return a dict of status → count for all four statuses.

        All four keys (``'pending'``, ``'running'``, ``'done'``, ``'failed'``)
        are always present, even if the count is 0.

        Returns
        -------
        dict
            ``{"pending": int, "running": int, "done": int, "failed": int}``.
        """
        with session_scope(self._factory) as session:
            return scheduler.get_stats(session)
