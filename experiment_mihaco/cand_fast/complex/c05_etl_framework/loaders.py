"""
loaders.py — SQLAlchemy loader that persists a DataFrame to an in-memory SQLite DB.
"""
from __future__ import annotations

from typing import List

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text


class SQLiteLoader:
    """Loads a DataFrame into an in-memory SQLite database using SQLAlchemy 2.0."""

    def __init__(self) -> None:
        # Use check_same_thread=False to allow use from multiple contexts if needed.
        self._engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        self._loaded = False

    def load(self, df: pd.DataFrame, table_name: str) -> None:
        """Persist df to the SQLite table. Replaces existing data."""
        with self._engine.connect() as conn:
            df.to_sql(table_name, con=conn, if_exists="replace", index=False)
            conn.commit()
        self._loaded = True

    def query(self, sql: str) -> List[dict]:
        """Execute a raw SQL string and return a list of row dicts.

        Raises RuntimeError if load() has not been called yet.
        """
        if not self._loaded:
            raise RuntimeError(
                "Pipeline.query() called before Pipeline.run(). Call run() first."
            )
        with self._engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row._mapping) for row in result]
        return rows
