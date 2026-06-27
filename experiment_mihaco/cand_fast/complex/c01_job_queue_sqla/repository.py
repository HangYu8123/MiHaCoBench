"""Engine and session factory helpers for the job queue."""

import sys
import os

# Ensure the task directory is on sys.path for absolute-style imports
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import Session
from models import Base


def create_engine(url: str):
    """Create and return a SQLAlchemy engine for the given URL."""
    engine = _create_engine(url)
    return engine


def init_db(engine) -> None:
    """Create all ORM tables against the given engine."""
    Base.metadata.create_all(engine)


def get_session(engine) -> Session:
    """Return a new Session bound to engine (caller must use as context manager)."""
    return Session(engine)
