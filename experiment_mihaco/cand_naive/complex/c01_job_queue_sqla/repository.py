"""Low-level DB access helpers (session management)."""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import Base


def create_db_engine(url: str = "sqlite:///:memory:"):
    """Create and return a SQLAlchemy engine."""
    engine = create_engine(url, echo=False)
    return engine


def init_db(engine):
    """Create all ORM tables."""
    Base.metadata.create_all(engine)


def get_session_factory(engine):
    """Return a session factory bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=True, autocommit=False)


@contextmanager
def session_scope(session_factory):
    """Provide a transactional scope around a series of operations."""
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
