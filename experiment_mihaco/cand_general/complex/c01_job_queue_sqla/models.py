"""SQLAlchemy 2.0 ORM models for the priority job queue.

Exports:
    Base        — DeclarativeBase subclass shared by all models.
    Job         — Mapped class for the ``jobs`` table.
    Dependency  — Mapped class for the ``dependencies`` table.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base."""
    pass


class Job(Base):
    """A single unit of work enqueued in the job queue.

    Columns
    -------
    id          Primary key, auto-incremented.
    name        Human-readable job name; required.
    payload     Optional JSON-serialised dict stored as Text.
                SQL NULL when the caller passed ``None``.
    priority    Scheduling priority; higher value = higher priority.
                Defaults to 0.
    status      Lifecycle state: ``'pending'``, ``'running'``,
                ``'done'``, or ``'failed'``.
    attempts    Number of times ``fail()`` has retried this job so far.
                Starts at 0.
    result      Optional JSON-serialised dict stored as Text.
                Populated by ``complete()``; NULL otherwise.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Job id={self.id!r} name={self.name!r} "
            f"status={self.status!r} priority={self.priority!r}>"
        )


class Dependency(Base):
    """Records that *job_id* must wait for *depends_on_id* to be ``'done'``.

    The composite primary key ``(job_id, depends_on_id)`` prevents duplicate
    dependency rows from being inserted.
    """

    __tablename__ = "dependencies"

    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id"), primary_key=True
    )
    depends_on_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id"), primary_key=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dependency job_id={self.job_id!r} depends_on_id={self.depends_on_id!r}>"
