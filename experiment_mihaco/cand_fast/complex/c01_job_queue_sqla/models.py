"""SQLAlchemy 2.0 ORM models for the priority job queue.

Defines:
    Base        — declarative base class
    Job         — job table
    Dependency  — dependency edges table
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""


class Job(Base):
    """Represents a single job in the queue.

    Columns
    -------
    id        : auto-increment primary key
    name      : human-readable job name
    payload   : optional JSON dict passed to the worker
    priority  : scheduling priority; higher value = higher urgency
    status    : one of "pending", "running", "done", "failed"
    attempts  : number of failed attempts recorded via fail()
    result    : optional JSON dict written back by complete()
    """

    __tablename__ = "job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Job id={self.id!r} name={self.name!r} "
            f"status={self.status!r} priority={self.priority!r}>"
        )


class Dependency(Base):
    """Records a dependency edge: job ``job_id`` must wait for ``depends_on_id``.

    The composite primary key (job_id, depends_on_id) prevents duplicate edges.
    """

    __tablename__ = "dependency"

    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job.id"), primary_key=True, nullable=False
    )
    depends_on_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job.id"), primary_key=True, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dependency job_id={self.job_id!r} depends_on_id={self.depends_on_id!r}>"
