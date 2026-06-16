"""loaders.py — SQLAlchemy loader that persists a DataFrame to an in-memory DB."""

from __future__ import annotations

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text


class SQLAlchemyLoader:
    """Loads a DataFrame into a SQLAlchemy in-memory SQLite database."""

    def __init__(self, table_name: str, engine: sa.Engine | None = None) -> None:
        self.table_name = table_name
        if engine is None:
            engine = sa.create_engine("sqlite:///:memory:", future=True)
        self.engine = engine
        self._loaded = False

    def load(self, df: pd.DataFrame) -> None:
        """Persist the DataFrame to the database table.

        Uses if_exists='replace' so repeated calls are idempotent.
        """
        df.to_sql(
            self.table_name,
            con=self.engine,
            if_exists="replace",
            index=False,
        )
        self._loaded = True

    def query(self, sql: str) -> list[dict]:
        """Execute a SQL string and return a list of row dicts.

        Raises RuntimeError if load() has not been called yet.
        """
        if not self._loaded:
            raise RuntimeError(
                "query() called before run(). Call run() first to load data."
            )
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
