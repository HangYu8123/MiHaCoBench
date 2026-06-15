"""Low-level database access helpers for the priority job queue.

This module provides:
    make_engine   — create a SQLAlchemy engine and initialise the schema
    make_session  — sessionmaker factory builder

Callers should import these helpers rather than constructing engine/session
objects directly.
"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base


def make_engine(url: str = "sqlite:///:memory:") -> Engine:
    """Create a SQLAlchemy engine and ensure all ORM tables exist.

    Parameters
    ----------
    url:
        SQLAlchemy database URL.  Defaults to an in-process SQLite database.

    Returns
    -------
    Engine
        A ready-to-use SQLAlchemy 2.0 :class:`Engine`.
    """
    engine = create_engine(url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def make_session(engine: Engine) -> sessionmaker[Session]:
    """Return a :class:`sessionmaker` factory bound to *engine*.

    Parameters
    ----------
    engine:
        An engine previously created by :func:`make_engine`.

    Returns
    -------
    sessionmaker[Session]
        A callable that produces :class:`Session` instances.  Typical usage::

            Session = make_session(engine)
            with Session() as session:
                ...
                session.commit()
    """
    return sessionmaker(bind=engine, expire_on_commit=False)
