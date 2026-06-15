"""loaders.py — SQLAlchemy loader for persisting a DataFrame to an in-memory DB."""
from __future__ import annotations

from typing import Any

import pandas as pd
import sqlalchemy as sa


class SQLAlchemyLoader:
    """Load a DataFrame into a SQLAlchemy-backed database table."""

    def __init__(self, url: str = "sqlite:///:memory:") -> None:
        self._engine = sa.create_engine(url, echo=False)
        self._loaded = False
        self._table_name: str | None = None

    def load(self, df: pd.DataFrame, table_name: str) -> None:
        df.to_sql(
            name=table_name,
            con=self._engine,
            if_exists="replace",
            index=False,
        )
        self._table_name = table_name
        self._loaded = True

    def query(self, sql: str) -> list[dict[str, Any]]:
        if not self._loaded:
            raise RuntimeError(
                "SQLAlchemyLoader.query() called before load() — "
                "run the pipeline first."
            )
        with self._engine.connect() as conn:
            result = conn.execute(sa.text(sql))
            keys = list(result.keys())
            return [dict(zip(keys, row)) for row in result.fetchall()]

    @property
    def engine(self) -> sa.Engine:
        return self._engine

    @property
    def is_loaded(self) -> bool:
        return self._loaded
