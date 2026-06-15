"""Low-level database access helpers for the job queue.

Exports
-------
make_engine(url)              — Create a configured SQLAlchemy ``Engine``.
make_session_factory(engine)  — Return a ``sessionmaker`` bound to *engine*.
session_scope(factory)        — Context manager that yields a ``Session``
                                and commits on clean exit / rolls back on
                                exception.

SQLite special handling
-----------------------
* ``check_same_thread=False`` is passed so that SQLAlchemy's connection pool
  can hand the same connection to any thread without SQLite's built-in
  thread-guard raising ``ProgrammingError``.
* ``StaticPool`` is used for in-memory URLs so that every ``Session`` shares
  **the same single connection**.  Without this, each session checkout would
  open a fresh connection to a brand-new empty in-memory database, discarding
  all previously written data.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def make_engine(url: str) -> Engine:
    """Create and return a SQLAlchemy *Engine* for *url*.

    Parameters
    ----------
    url:
        A SQLAlchemy database URL, e.g. ``"sqlite:///:memory:"`` or
        ``"sqlite:///jobs.db"``.

    Returns
    -------
    Engine
        A configured engine ready for use.
    """
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a ``sessionmaker`` bound to *engine*.

    Parameters
    ----------
    engine:
        A SQLAlchemy ``Engine`` (e.g. from :func:`make_engine`).

    Returns
    -------
    sessionmaker
        A callable that produces ``Session`` instances.
    """
    return sessionmaker(bind=engine)


@contextmanager
def session_scope(
    factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    """Context manager that opens a ``Session``, yields it, and finalises it.

    On **clean exit** the session is committed then closed.
    On **exception** the session is rolled back then closed, and the
    exception is re-raised.

    Usage::

        with session_scope(factory) as session:
            session.add(some_object)
            # commit happens automatically at block exit

    Parameters
    ----------
    factory:
        A ``sessionmaker`` instance (from :func:`make_session_factory`).

    Yields
    ------
    Session
        An open SQLAlchemy ORM session.
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
