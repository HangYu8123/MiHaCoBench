"""loaders.py — SQLAlchemy loader for persisting a DataFrame to an in-memory DB."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class SQLiteLoader:
    """Loads a DataFrame into an in-memory SQLite database via SQLAlchemy 2.0."""

    def __init__(self) -> None:
        self._engine: Engine = create_engine("sqlite:///:memory:")
        self._table: str | None = None
        self._loaded: bool = False

    def load(self, df: pd.DataFrame, table: str) -> None:
        """Persist df to the named table. Uses if_exists='replace' for idempotency."""
        self._table = table
        df.to_sql(table, con=self._engine, if_exists="replace", index=False)
        self._loaded = True

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def loaded(self) -> bool:
        return self._loaded

    def query(self, sql: str) -> list[dict]:
        """Execute a raw SQL string and return a list of row dicts."""
        if not self._loaded:
            raise RuntimeError("query() called before run(); call run() first.")
        with self._engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
