"""pipeline.py — Public facade class Pipeline."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pandas as pd

from config import (
    AggregateConfig,
    FilterConfig,
    parse_yaml,
)
from loaders import SQLiteLoader
from transforms import TRANSFORM_REGISTRY


class Pipeline:
    """YAML-driven ETL pipeline: extract CSV → apply transforms → load to SQLite."""

    def __init__(self, config, data_dir: Optional[str]) -> None:
        self._config = config
        self._data_dir = data_dir
        self._loader = SQLiteLoader()
        self._ran = False

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: Optional[str] = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline.

        ``data_dir`` is prepended to a relative CSV path in the extract section.
        If the CSV path is already absolute, ``data_dir`` is ignored.
        """
        config = parse_yaml(yaml_text)
        return cls(config, data_dir)

    def run(self) -> pd.DataFrame:
        """Execute the full pipeline: extract → transform → load → return.

        Reads the CSV specified in ``extract``, applies each transform in order,
        loads the final DataFrame into the SQLAlchemy table named in ``load``,
        and returns the final DataFrame.

        Raises ``ValueError`` if a column required by a transform step is missing
        from the DataFrame at the point where that step is applied.
        """
        # --- Extract ---
        csv_path = self._config.extract.csv
        if not os.path.isabs(csv_path) and self._data_dir is not None:
            csv_path = os.path.join(self._data_dir, csv_path)

        df = pd.read_csv(csv_path)

        # --- Pre-loop validation: filter columns only ---
        # Per spec: "After loading the CSV but before applying transforms,
        # raise ValueError if the filter column is not in the DataFrame."
        for tc in self._config.transforms:
            if isinstance(tc, FilterConfig):
                if tc.column not in df.columns:
                    raise ValueError(
                        f"Filter column {tc.column!r} not found in DataFrame. "
                        f"Available columns: {list(df.columns)}"
                    )

        # --- Transform loop ---
        for tc in self._config.transforms:
            # Aggregate validation: done "at the time the aggregate step is applied"
            if isinstance(tc, AggregateConfig):
                missing = [
                    col
                    for col in (list(tc.group_by) + list(tc.agg.keys()))
                    if col not in df.columns
                ]
                if missing:
                    raise ValueError(
                        f"Aggregate columns not found in DataFrame: {missing}. "
                        f"Available columns: {list(df.columns)}"
                    )

            # Build and apply the transform
            op = tc.op
            transform_cls = TRANSFORM_REGISTRY[op]
            transform = transform_cls(tc)
            df = transform.apply(df)

        # --- Load ---
        self._loader.load(df, self._config.load.table)
        self._ran = True

        return df

    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL string against the loaded table.

        Returns a list of row dicts (column name → Python value). ``run()``
        must have been called first; raises ``RuntimeError`` if not.
        """
        if not self._ran:
            raise RuntimeError(
                "Pipeline.run() must be called before Pipeline.query()."
            )
        return self._loader.query(sql)
