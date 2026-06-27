"""SQLAlchemy 2.0 ORM models for the job queue."""

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships for dependencies
    # Dependencies where this job is the dependent (the job that needs others to be done)
    dependencies: Mapped[list["Dependency"]] = relationship(
        "Dependency",
        foreign_keys="Dependency.job_id",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Dependency(Base):
    __tablename__ = "dependencies"

    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id"), primary_key=True
    )
    depends_on_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id"), primary_key=True
    )

    job: Mapped["Job"] = relationship(
        "Job", foreign_keys=[job_id], back_populates="dependencies"
    )
    depends_on_job: Mapped["Job"] = relationship(
        "Job", foreign_keys=[depends_on_id]
    )
