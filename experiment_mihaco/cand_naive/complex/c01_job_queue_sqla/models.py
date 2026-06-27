"""SQLAlchemy 2.0 ORM models for the priority job queue."""

import json
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    payload = Column(Text, nullable=True)   # stored as JSON string
    priority = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    result = Column(Text, nullable=True)    # stored as JSON string

    # relationships
    dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.job_id",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def get_payload(self):
        if self.payload is None:
            return None
        return json.loads(self.payload)

    def set_payload(self, value):
        if value is None:
            self.payload = None
        else:
            self.payload = json.dumps(value)

    def get_result(self):
        if self.result is None:
            return None
        return json.loads(self.result)

    def set_result(self, value):
        if value is None:
            self.result = None
        else:
            self.result = json.dumps(value)


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    depends_on_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("job_id", "depends_on_id", name="uq_dep"),
    )

    job = relationship("Job", foreign_keys=[job_id], back_populates="dependencies")
    depends_on_job = relationship("Job", foreign_keys=[depends_on_id])
