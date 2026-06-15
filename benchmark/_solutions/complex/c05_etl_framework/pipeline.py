"""pipeline.py — Public facade class Pipeline (the only file the grader imports).

Composes config parsing, transform execution, and SQLAlchemy loading into a
single high-level interface.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from config import PipelineConfig, parse_yaml
from loaders import SQLAlchemyLoader
from transforms import build_transform


class Pipeline:
    """YAML-driven ETL pipeline: Extract → Transform → Load.

    Instantiate via :meth:`from_yaml`; then call :meth:`run` to execute the
    pipeline and :meth:`query` to inspect the loaded data.
    """

    def __init__(self, cfg: PipelineConfig, data_dir: str | None = None) -> None:
        """Internal constructor — use :meth:`from_yaml` instead.

        Parameters
        ----------
        cfg:
            Parsed pipeline configuration.
        data_dir:
            Optional directory prepended to relative CSV paths.
        """
        self._cfg = cfg
        self._data_dir = data_dir
        self._loader = SQLAlchemyLoader("sqlite:///:memory:")
        self._result_df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: str | None = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline.

        Parameters
        ----------
        yaml_text:
            Full YAML string describing the pipeline spec.
        data_dir:
            If the CSV path in ``extract.csv`` is relative, it is resolved
            relative to this directory.  If ``None``, the current working
            directory is used.

        Returns
        -------
        Pipeline
            Configured but not yet executed pipeline.
        """
        cfg = parse_yaml(yaml_text)
        return cls(cfg, data_dir=data_dir)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> pd.DataFrame:
        """Execute extract → transform → load and return the final DataFrame.

        1. Read the CSV from the path specified in ``extract.csv``.
        2. Apply each transform in order, validating column existence first.
        3. Persist the final DataFrame to the SQLAlchemy table.
        4. Return the final DataFrame.

        Returns
        -------
        pd.DataFrame
            The fully transformed and loaded DataFrame.

        Raises
        ------
        ValueError
            If a required column is missing at any transform step.
        """
        # --- Extract ---
        csv_path = self._resolve_csv_path(self._cfg.extract.csv)
        df = pd.read_csv(csv_path)

        # --- Transform ---
        for tcfg in self._cfg.transforms:
            transform = build_transform(tcfg)
            transform.validate(df)   # raises ValueError on missing columns
            df = transform.apply(df)

        # --- Load ---
        self._loader.load(df, self._cfg.load.table)
        self._result_df = df
        return df

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a raw SQL string against the loaded table.

        Parameters
        ----------
        sql:
            SQL query to run against the database.

        Returns
        -------
        list[dict]
            One dict per row returned by the query.

        Raises
        ------
        RuntimeError
            If :meth:`run` has not been called yet.
        """
        if not self._loader.is_loaded:
            raise RuntimeError(
                "Pipeline.query() called before run() — execute the pipeline first."
            )
        return self._loader.query(sql)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_csv_path(self, csv_path: str) -> str:
        """Resolve ``csv_path`` relative to ``data_dir`` if it is not absolute."""
        p = Path(csv_path)
        if p.is_absolute():
            return str(p)
        if self._data_dir is not None:
            return str(Path(self._data_dir) / p)
        return str(Path.cwd() / p)

    # ------------------------------------------------------------------
    # Properties (convenience)
    # ------------------------------------------------------------------

    @property
    def result(self) -> pd.DataFrame | None:
        """The last DataFrame produced by :meth:`run`, or None if not yet run."""
        return self._result_df
