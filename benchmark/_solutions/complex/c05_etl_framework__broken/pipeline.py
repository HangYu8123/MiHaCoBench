"""pipeline.py — Public facade class Pipeline (broken reference).

This is the deliberately-broken reference for complex/c05_etl_framework.
The planted defect is in transforms.py (Aggregate uses wrong column).
This file is identical to the gold pipeline.py.
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
    """YAML-driven ETL pipeline: Extract → Transform → Load."""

    def __init__(self, cfg: PipelineConfig, data_dir: str | None = None) -> None:
        self._cfg = cfg
        self._data_dir = data_dir
        self._loader = SQLAlchemyLoader("sqlite:///:memory:")
        self._result_df: pd.DataFrame | None = None

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: str | None = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline."""
        cfg = parse_yaml(yaml_text)
        return cls(cfg, data_dir=data_dir)

    def run(self) -> pd.DataFrame:
        """Execute extract → transform → load and return the final DataFrame."""
        # --- Extract ---
        csv_path = self._resolve_csv_path(self._cfg.extract.csv)
        df = pd.read_csv(csv_path)

        # --- Transform ---
        for tcfg in self._cfg.transforms:
            transform = build_transform(tcfg)
            transform.validate(df)
            df = transform.apply(df)

        # --- Load ---
        self._loader.load(df, self._cfg.load.table)
        self._result_df = df
        return df

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a raw SQL string against the loaded table."""
        if not self._loader.is_loaded:
            raise RuntimeError(
                "Pipeline.query() called before run() — execute the pipeline first."
            )
        return self._loader.query(sql)

    def _resolve_csv_path(self, csv_path: str) -> str:
        p = Path(csv_path)
        if p.is_absolute():
            return str(p)
        if self._data_dir is not None:
            return str(Path(self._data_dir) / p)
        return str(Path.cwd() / p)

    @property
    def result(self) -> pd.DataFrame | None:
        return self._result_df
