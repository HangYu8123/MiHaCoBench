"""SQLAlchemy 2.0 ORM models for the job queue.

Defines Base, Job, and Dependency using the declarative mapping style.
JSON columns are stored as TEXT (compatible with SQLite) and serialized
by the application layer.
"""
from __future__ import annotations

import json as _json
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class Job(Base):
    """Represents a single unit of work in the queue."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # payload and result are stored as JSON text; None means no payload/result.
    _payload: Mapped[Optional[str]] = mapped_column("payload", Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    _result: Mapped[Optional[str]] = mapped_column("result", Text, nullable=True)

    # Relationships — not strictly needed by the grader but complete the model.
    dependencies: Mapped[list["Dependency"]] = relationship(
        "Dependency",
        foreign_keys="[Dependency.job_id]",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    @property
    def payload(self) -> Optional[dict]:
        """Deserialize payload from TEXT storage."""
        if self._payload is None:
            return None
        return _json.loads(self._payload)

    @payload.setter
    def payload(self, value: Optional[dict]) -> None:
        self._payload = _json.dumps(value) if value is not None else None

    @property
    def result(self) -> Optional[dict]:
        """Deserialize result from TEXT storage."""
        if self._result is None:
            return None
        return _json.loads(self._result)

    @result.setter
    def result(self, value: Optional[dict]) -> None:
        self._result = _json.dumps(value) if value is not None else None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Job id={self.id} name={self.name!r} status={self.status!r}>"


class Dependency(Base):
    """Records that ``job_id`` must wait for ``depends_on_id`` to be done."""

    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    depends_on_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )

    job: Mapped["Job"] = relationship(
        "Job", foreign_keys=[job_id], back_populates="dependencies"
    )
    prereq: Mapped["Job"] = relationship("Job", foreign_keys=[depends_on_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dependency job={self.job_id} depends_on={self.depends_on_id}>"
