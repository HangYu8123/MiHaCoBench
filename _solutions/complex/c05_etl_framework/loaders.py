"""loaders.py — SQLAlchemy loader for persisting a DataFrame to an in-memory DB.

Uses pandas ``DataFrame.to_sql`` backed by a SQLAlchemy 2.0 engine so the
entire ETL pipeline stores its final result in a queryable in-memory SQLite DB.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import sqlalchemy as sa


class SQLAlchemyLoader:
    """Load a DataFrame into a SQLAlchemy-backed database table.

    Parameters
    ----------
    url:
        SQLAlchemy database URL.  Defaults to ``"sqlite:///:memory:"``.
    """

    def __init__(self, url: str = "sqlite:///:memory:") -> None:
        self._engine = sa.create_engine(url, echo=False)
        self._loaded = False
        self._table_name: str | None = None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def load(self, df: pd.DataFrame, table_name: str) -> None:
        """Persist ``df`` to ``table_name`` (replacing any existing data).

        Parameters
        ----------
        df:
            The transformed DataFrame to persist.
        table_name:
            Target table name in the database.
        """
        df.to_sql(
            name=table_name,
            con=self._engine,
            if_exists="replace",
            index=False,
        )
        self._table_name = table_name
        self._loaded = True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a raw SQL string and return rows as a list of dicts.

        Parameters
        ----------
        sql:
            SQL query string to execute against the database.

        Returns
        -------
        list[dict]
            Each element is a mapping of column name → Python value for one row.

        Raises
        ------
        RuntimeError
            If :meth:`load` has not been called yet.
        """
        if not self._loaded:
            raise RuntimeError(
                "SQLAlchemyLoader.query() called before load() — "
                "run the pipeline first."
            )
        with self._engine.connect() as conn:
            result = conn.execute(sa.text(sql))
            keys = list(result.keys())
            return [dict(zip(keys, row)) for row in result.fetchall()]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def engine(self) -> sa.Engine:
        """The underlying SQLAlchemy engine."""
        return self._engine

    @property
    def is_loaded(self) -> bool:
        """True after a successful :meth:`load` call."""
        return self._loaded
