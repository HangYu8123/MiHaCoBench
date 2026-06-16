"""loaders.py — SQLAlchemy loader that persists a DataFrame to an in-memory DB."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine


class SQLAlchemyLoader:
    """Load a DataFrame into a SQLAlchemy table (in-memory SQLite)."""

    def __init__(self, table_name: str, engine: Engine) -> None:
        self.table_name = table_name
        self.engine = engine

    def load(self, df: pd.DataFrame) -> None:
        """Write df to the configured table, replacing any existing data."""
        df.to_sql(
            self.table_name,
            con=self.engine,
            if_exists="replace",
            index=False,
        )
