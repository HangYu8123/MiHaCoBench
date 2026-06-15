"""Low-level database access helpers for the priority job queue.

Provides:
  - create_engine_and_tables: build an engine and materialise all ORM tables
  - session_scope: context manager that commits on success or rolls back on error
  - get_job: fetch a single Job by primary key (raises KeyError if missing)
  - add_job: persist a new Job and return its assigned id
  - add_dependency: persist a Dependency edge
  - list_pending_jobs_with_deps: return all pending jobs together with their
    dependency prerequisite ids, used by the scheduler for claimability checks
  - count_by_status: return a dict of status -> count for stats
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Dependency, Job


def create_engine_and_tables(url: str) -> Engine:
    """Create and return an SQLAlchemy engine; also creates all ORM tables.

    Parameters
    ----------
    url:
        SQLAlchemy database URL (e.g. ``"sqlite:///:memory:"``).

    Returns
    -------
    Engine
        Configured engine with the schema already created.
    """
    # connect_args=check_same_thread is False so in-memory SQLite can be used
    # from the same thread across multiple Session calls (typical single-thread use).
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(url, connect_args=connect_args, echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker:
    """Return a ``sessionmaker`` bound to *engine*."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope(factory: sessionmaker) -> Generator[Session, None, None]:
    """Yield a transactional session and commit on success or rollback on error.

    Usage::

        with session_scope(session_factory) as session:
            session.add(some_object)
    """
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_job(session: Session, job_id: int) -> Job:
    """Return the ``Job`` with the given *job_id*, or raise ``KeyError``."""
    job = session.get(Job, job_id)
    if job is None:
        raise KeyError(f"No job with id={job_id!r}")
    return job


def add_job(
    session: Session,
    name: str,
    payload_json: str | None,
    priority: int,
) -> Job:
    """Insert a new ``Job`` row (caller must commit the session).

    The job's ``_payload`` column is set directly (already JSON-encoded or NULL).
    Returns the ``Job`` instance (``id`` is available after flush).
    """
    job = Job(
        name=name,
        _payload=payload_json,
        priority=priority,
        status="pending",
        attempts=0,
        _result=None,
    )
    session.add(job)
    session.flush()  # populate job.id
    return job


def add_dependency(session: Session, job_id: int, depends_on_id: int) -> None:
    """Insert a ``Dependency`` edge (caller must commit the session)."""
    dep = Dependency(job_id=job_id, depends_on_id=depends_on_id)
    session.add(dep)


def count_by_status(session: Session) -> dict:
    """Return ``{status: count}`` for every status that appears in the Job table.

    Always includes all four canonical statuses with a 0 default.
    """
    rows = (
        session.execute(
            select(Job.status, func.count(Job.id).label("cnt")).group_by(Job.status)
        )
        .mappings()
        .all()
    )
    result: dict = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    for row in rows:
        result[row["status"]] = row["cnt"]
    return result
