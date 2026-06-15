"""SQLAlchemy 2.0 ORM models for the priority job queue.

Defines:
  - Base: declarative base for all ORM models
  - Job: a unit of work with priority, status, retry logic, and optional payload/result
  - Dependency: a directed edge (job_id -> depends_on_id) representing a prerequisite
"""

import json
from typing import Any

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Declarative base class shared by all ORM models."""
    pass


class _JSONEncodedText:
    """Mixin that transparently serialises/deserialises a dict to/from a TEXT column.

    SQLAlchemy's built-in JSON type is not supported equally across all dialects
    when targeting SQLite 3.x shipped with older CPython builds.  Storing JSON as
    plain TEXT is the safest cross-version approach.
    """
    # Not a real SQLAlchemy type; we handle conversion in property accessors.
    pass


class Job(Base):
    """Represents a single unit of work in the queue.

    Columns
    -------
    id          : auto-incremented primary key
    name        : human-readable label for the job
    _payload    : JSON-serialised dict stored as TEXT (may be NULL)
    priority    : scheduling priority; higher value = claimed first (default 0)
    status      : one of 'pending', 'running', 'done', 'failed'
    attempts    : number of times this job has been claimed and failed
    _result     : JSON-serialised dict stored as TEXT (may be NULL)
    """

    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    _payload = Column("payload", Text, nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    status = Column(String(16), nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    _result = Column("result", Text, nullable=True)

    # Relationships
    # dependencies: rows where THIS job is the dependent (i.e. things *this* job waits on)
    dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.job_id",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    @property
    def payload(self) -> dict | None:
        """Return the payload dict (or None if not set)."""
        if self._payload is None:
            return None
        return json.loads(self._payload)

    @payload.setter
    def payload(self, value: dict | None) -> None:
        """Serialise a dict to JSON text for storage."""
        if value is None:
            self._payload = None
        else:
            self._payload = json.dumps(value, separators=(",", ":"))

    @property
    def result(self) -> dict | None:
        """Return the result dict (or None if not set)."""
        if self._result is None:
            return None
        return json.loads(self._result)

    @result.setter
    def result(self, value: dict | None) -> None:
        """Serialise a dict to JSON text for storage."""
        if value is None:
            self._result = None
        else:
            self._result = json.dumps(value, separators=(",", ":"))

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Job id={self.id!r} name={self.name!r} "
            f"status={self.status!r} priority={self.priority!r}>"
        )


class Dependency(Base):
    """Records a prerequisite edge: ``job_id`` depends on ``depends_on_id``.

    A job is only claimable when *all* rows with ``job_id = X`` have their
    corresponding ``depends_on_id`` pointing at a job whose status is ``'done'``.
    """

    __tablename__ = "dependency"
    __table_args__ = (
        UniqueConstraint("job_id", "depends_on_id", name="uq_dependency"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("job.id", ondelete="CASCADE"), nullable=False)
    depends_on_id = Column(
        Integer, ForeignKey("job.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    job = relationship("Job", foreign_keys=[job_id], back_populates="dependencies")
    prerequisite = relationship("Job", foreign_keys=[depends_on_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dependency job_id={self.job_id!r} depends_on_id={self.depends_on_id!r}>"
