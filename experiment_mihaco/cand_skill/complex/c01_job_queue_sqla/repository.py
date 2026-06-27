"""Low-level DB access helpers: engine creation and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def make_engine(url: str = "sqlite:///:memory:"):
    """Create a SQLAlchemy engine.

    For SQLite in-memory databases, StaticPool ensures all operations share
    the same underlying connection (so the DB survives across session opens).
    """
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


def make_session_factory(engine):
    """Return a sessionmaker bound to the given engine."""
    return sessionmaker(engine)


def get_session(session_factory):
    """Open and return a new session. Caller is responsible for closing."""
    return session_factory()
