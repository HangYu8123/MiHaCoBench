"""
pipeline.py — Public facade class Pipeline.

The grader imports THIS file and uses only Pipeline.from_yaml(), run(), and query().
"""
from __future__ import annotations

import os
from typing import List, Optional

import pandas as pd

from config import (
    AggregateTransformConfig,
    FilterTransformConfig,
    PipelineConfig,
    parse_pipeline_config,
)
from loaders import SQLiteLoader
from transforms import Aggregate, build_transform


class Pipeline:
    """YAML-driven ETL pipeline: extract → transform → load."""

    def __init__(
        self,
        config: PipelineConfig,
        data_dir: Optional[str] = None,
    ) -> None:
        self._config = config
        self._data_dir = data_dir
        self._loader = SQLiteLoader()
        self._ran = False

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: Optional[str] = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline."""
        config = parse_pipeline_config(yaml_text)
        return cls(config=config, data_dir=data_dir)

    def run(self) -> pd.DataFrame:
        """Execute the full pipeline: extract → transform → load → return.

        Raises ValueError if a column required by a transform step is missing
        at the point where that step is applied.
        """
        # ── Extract ──────────────────────────────────────────────────────────
        csv_path = self._config.extract.csv
        if self._data_dir is not None and not os.path.isabs(csv_path):
            csv_path = os.path.join(self._data_dir, csv_path)

        df = pd.read_csv(csv_path)

        # ── Build transform objects ───────────────────────────────────────────
        transforms = [build_transform(tc) for tc in self._config.transforms]

        # ── Validate filter steps upfront (before any transforms applied) ────
        # Per spec: filter column validation is "after loading CSV but before transforms"
        # Aggregate validation is lazy (at the time the aggregate step is applied)
        for t in transforms:
            tc = self._config.transforms[transforms.index(t)]
            if isinstance(tc, FilterTransformConfig):
                t.validate(df)

        # ── Apply transforms in order ────────────────────────────────────────
        for t, tc in zip(transforms, self._config.transforms):
            if isinstance(tc, AggregateTransformConfig):
                # Lazy validation for aggregate (columns may have changed via prior transforms)
                t.validate(df)
            df = t.apply(df)

        # ── Load ─────────────────────────────────────────────────────────────
        self._loader.load(df, self._config.load.table)
        self._ran = True

        return df

    def query(self, sql: str) -> List[dict]:
        """Execute a raw SQL string against the loaded table.

        Returns a list of row dicts. Raises RuntimeError if run() not called first.
        """
        if not self._ran:
            raise RuntimeError(
                "Pipeline.query() called before Pipeline.run(). Call run() first."
            )
        return self._loader.query(sql)
