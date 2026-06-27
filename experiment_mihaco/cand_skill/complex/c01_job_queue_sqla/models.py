"""SQLAlchemy 2.0 ORM models for the priority job queue."""

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "job"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String, nullable=False)
    payload = mapped_column(Text, nullable=True)
    priority = mapped_column(Integer, default=0, nullable=False)
    status = mapped_column(String, default="pending", nullable=False)
    attempts = mapped_column(Integer, default=0, nullable=False)
    result = mapped_column(Text, nullable=True)


class Dependency(Base):
    __tablename__ = "dependency"

    job_id = mapped_column(Integer, ForeignKey("job.id"), primary_key=True)
    depends_on_id = mapped_column(Integer, ForeignKey("job.id"), primary_key=True)
