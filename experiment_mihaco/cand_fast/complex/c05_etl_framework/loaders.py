"""loaders.py — SQLAlchemy loader that persists a DataFrame to an in-memory DB."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine


class SQLAlchemyLoader:
    """Loads a DataFrame into a SQLAlchemy-managed table."""

    def __init__(self, engine: Engine, table: str) -> None:
        self.engine = engine
        self.table = table

    def load(self, df: pd.DataFrame) -> None:
        """Write df to the configured table, replacing existing data."""
        df.to_sql(self.table, con=self.engine, if_exists="replace", index=False)
