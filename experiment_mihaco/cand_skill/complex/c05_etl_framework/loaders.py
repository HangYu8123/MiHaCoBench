"""loaders.py — SQLAlchemy loader using an in-memory SQLite database."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import create_engine, text


class SQLiteLoader:
    """Load a DataFrame into an in-memory SQLite database and support SQL queries."""

    def __init__(self) -> None:
        # Use check_same_thread=False to allow use across methods without issues
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )

    def load(self, df: pd.DataFrame, table_name: str) -> None:
        """Write df to the named table, replacing any existing data."""
        df.to_sql(table_name, self.engine, if_exists="replace", index=False)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as a list of plain dicts."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row) for row in result.mappings()]
