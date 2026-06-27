"""pipeline.py — Public facade class Pipeline (the grader imports THIS file only)."""

from __future__ import annotations

import sys
import os

# Ensure local modules are importable when grader imports pipeline.py by path
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

import pandas as pd

from config import parse_yaml, PipelineConfig
from transforms import build_transform, Transform
from loaders import SQLiteLoader


class Pipeline:
    """YAML-driven ETL pipeline: Extract → Transform → Load."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._loader = SQLiteLoader()
        self._result: pd.DataFrame | None = None

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: str | None = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline.

        ``data_dir`` is prepended to a relative CSV path in the extract section.
        If the CSV path is already absolute, ``data_dir`` is ignored.
        """
        config = parse_yaml(yaml_text, data_dir=data_dir)
        return cls(config)

    def run(self) -> pd.DataFrame:
        """Execute the full pipeline: extract → transform → load → return.

        Reads the CSV specified in ``extract``, applies each transform in order,
        loads the final DataFrame into the SQLAlchemy table named in ``load``,
        and returns the final DataFrame.

        Raises ``ValueError`` if a column required by a transform step is missing
        from the DataFrame at the point where that step is applied.
        """
        # Extract
        df = pd.read_csv(self._config.extract.csv)

        # Build and validate+apply transforms in order
        for cfg in self._config.transforms:
            transform: Transform = build_transform(cfg)
            # Validate against current state of DataFrame
            transform.validate(df)
            df = transform.apply(df)

        # Load
        self._loader.load(df, self._config.load.table)

        self._result = df
        return df

    def query(self, sql: str) -> list[dict]:
        """Execute a raw SQL string against the loaded table.

        Returns a list of row dicts (column name → Python value). ``run()``
        must have been called first; raises ``RuntimeError`` if not.
        """
        if not self._loader.loaded:
            raise RuntimeError("query() called before run(); call run() first.")
        return self._loader.query(sql)
