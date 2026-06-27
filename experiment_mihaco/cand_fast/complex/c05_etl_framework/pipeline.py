"""pipeline.py — Public facade class Pipeline for the YAML-driven ETL framework."""

from __future__ import annotations

import os

import pandas as pd
import sqlalchemy
from sqlalchemy import text

from config import parse_config, PipelineConfig
from transforms import build_transform, FilterRows, RenameColumns, Aggregate
from loaders import SQLAlchemyLoader


class Pipeline:
    """Orchestrates YAML-configured extract → transform → load pipelines."""

    def __init__(self, config: PipelineConfig, engine: sqlalchemy.engine.Engine) -> None:
        self._config = config
        self._engine = engine
        self._ran = False

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: str | None = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline.

        ``data_dir`` is prepended to a relative CSV path in the extract section.
        If the CSV path is already absolute, ``data_dir`` is ignored.
        """
        config = parse_config(yaml_text)
        engine = sqlalchemy.create_engine("sqlite:///:memory:")
        instance = cls(config=config, engine=engine)
        instance._data_dir = data_dir
        return instance

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
        data_dir = getattr(self, "_data_dir", None)
        if not os.path.isabs(csv_path) and data_dir is not None:
            csv_path = os.path.join(data_dir, csv_path)
        df = pd.read_csv(csv_path)

        # --- Upfront validation for filter and rename steps ---
        # Per spec: "After loading the CSV but before applying transforms, raise
        # ValueError if any column... does not exist in the DataFrame."
        # For filter: validate column against initial df.
        # For rename: validate source keys against initial df.
        # For aggregate: spec says "at the time the aggregate step is applied"
        #   (so aggregate validates lazily, after renames/derives may have changed cols).
        # For derive: no explicit upfront column validation required by spec.
        for step in self._config.transforms:
            transform = build_transform(step.op, step.params)
            if isinstance(transform, (FilterRows, RenameColumns)):
                transform.validate(df)

        # --- Transform ---
        transforms = [
            build_transform(step.op, step.params)
            for step in self._config.transforms
        ]
        for transform in transforms:
            # Aggregate validates at apply-time (validate() is called inside apply())
            # FilterRows and RenameColumns were already validated upfront;
            # calling apply() will re-validate but that's consistent.
            df = transform.apply(df)

        # --- Load ---
        loader = SQLAlchemyLoader(engine=self._engine, table=self._config.load.table)
        loader.load(df)

        self._ran = True
        return df

    def query(self, sql: str) -> list[dict]:
        """Execute a raw SQL string against the loaded table.

        Returns a list of row dicts (column name → Python value). ``run()``
        must have been called first; raises ``RuntimeError`` if not.
        """
        if not self._ran:
            raise RuntimeError("run() must be called before query()")
        with self._engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(r._mapping) for r in result.fetchall()]
        return rows
