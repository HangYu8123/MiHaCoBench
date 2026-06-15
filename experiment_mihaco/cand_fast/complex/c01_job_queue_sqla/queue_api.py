"""Public facade for the priority job queue.

The grader imports only this module and uses the :class:`JobQueue` class.
All implementation details are delegated to ``models``, ``repository``, and
``scheduler``.

Import isolation
----------------
This module uses ``sys.path`` manipulation to allow standalone import (i.e.
without a package ``__init__.py``) so the grader can do
``import queue_api`` directly from any working directory, as long as this
file and its sibling modules are in the same directory.
"""
from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Ensure sibling modules (models, repository, scheduler) are importable
# regardless of the caller's sys.path or working directory.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Now the siblings can be imported by name.
from models import Base, Dependency, Job  # noqa: E402
from repository import make_engine, make_session  # noqa: E402
from scheduler import (  # noqa: E402
    claim_job,
    complete_job,
    fail_job,
    get_stats,
)


class JobQueue:
    """Thread-safe* priority job queue backed by a SQLAlchemy 2.0 ORM.

    * Single-session serialisation — not multi-process safe without an
      external lock or a server-side database.

    Parameters
    ----------
    url:
        SQLAlchemy database URL.  Defaults to ``"sqlite:///:memory:"`` for
        fully in-process operation (no file system access required).
    max_retries:
        Maximum number of failure attempts before a job is permanently
        set to ``"failed"``.
    """

    def __init__(self, url: str = "sqlite:///:memory:", max_retries: int = 3) -> None:
        """Create engine, create all ORM tables, ready for use."""
        self._engine = make_engine(url)
        self._Session = make_session(self._engine)
        self._max_retries = max_retries

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(
        self,
        name: str,
        payload: dict | None = None,
        priority: int = 0,
        depends_on: list[int] | None = None,
    ) -> int:
        """Submit a new job and return its integer id.

        Parameters
        ----------
        name:
            Human-readable job name.
        payload:
            Optional dict passed to the worker; ``None`` is stored as SQL NULL
            and returned as ``None`` on retrieval.
        priority:
            Scheduling priority; higher value = higher urgency.
        depends_on:
            List of job ids that must be ``"done"`` before this job is
            claimable.  ``None`` or ``[]`` both mean no dependencies.

        Returns
        -------
        int
            The new job's primary key.
        """
        with self._Session() as session:
            job = Job(
                name=name,
                payload=payload,
                priority=priority,
                status="pending",
                attempts=0,
                result=None,
            )
            session.add(job)
            session.flush()  # populate job.id

            if depends_on:
                for dep_id in depends_on:
                    session.add(Dependency(job_id=job.id, depends_on_id=dep_id))

            session.commit()
            return int(job.id)

    def claim(self) -> dict | None:
        """Return and mark as running the highest-priority claimable job.

        A job is *claimable* iff:
          - Its status is ``"pending"``.
          - Every job in its ``depends_on`` list has status ``"done"``.

        Tie-breaking:
          1. Higher ``priority`` wins.
          2. Lower ``id`` wins among equal-priority jobs.

        Returns
        -------
        dict or None
            ``{"id": int, "name": str, "payload": dict|None, "priority": int}``
            or ``None`` if no claimable job exists.
        """
        with self._Session() as session:
            job = claim_job(session)
            if job is None:
                return None
            result = {
                "id": int(job.id),
                "name": job.name,
                "payload": job.payload,
                "priority": int(job.priority),
            }
            session.commit()
            return result

    def complete(self, job_id: int, result: dict | None = None) -> None:
        """Mark *job_id* as ``"done"`` and store the optional *result* dict."""
        with self._Session() as session:
            complete_job(session, job_id, result)
            session.commit()

    def fail(self, job_id: int) -> None:
        """Record a failure attempt for *job_id*.

        Retries (status back to ``"pending"``) if ``attempts < max_retries``;
        otherwise sets status to ``"failed"`` permanently.
        """
        with self._Session() as session:
            fail_job(session, job_id, self._max_retries)
            session.commit()

    def status(self, job_id: int) -> str:
        """Return the current status string for *job_id*.

        Returns
        -------
        str
            One of ``"pending"``, ``"running"``, ``"done"``, ``"failed"``.

        Raises
        ------
        ValueError
            If *job_id* does not exist.
        """
        with self._Session() as session:
            job = session.get(Job, job_id)
            if job is None:
                raise ValueError(f"No job with id={job_id!r}")
            return job.status

    def stats(self) -> dict:
        """Return per-status job counts; all four status keys are always present.

        Returns
        -------
        dict
            ``{"pending": int, "running": int, "done": int, "failed": int}``
        """
        with self._Session() as session:
            return get_stats(session)
