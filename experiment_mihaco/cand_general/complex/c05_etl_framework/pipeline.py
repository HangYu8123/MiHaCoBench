"""pipeline.py — Public facade class Pipeline for the YAML-driven ETL framework."""
from __future__ import annotations

import os
import re
import keyword
from typing import List, Optional

import pandas as pd
from sqlalchemy import create_engine, text

from config import parse_yaml
from transforms import REGISTRY, _extract_expr_columns
from loaders import SQLAlchemyLoader


class Pipeline:
    """YAML-driven ETL pipeline: extract CSV → transform → load to SQLite."""

    def __init__(self, csv_path: str, transforms, table_name: str, engine) -> None:
        self._csv_path = csv_path
        self._transforms = transforms
        self._table_name = table_name
        self.engine = engine
        self._ran = False

    @classmethod
    def from_yaml(cls, yaml_text: str, data_dir: Optional[str] = None) -> "Pipeline":
        """Parse a YAML pipeline spec and return a ready-to-run Pipeline.

        data_dir is prepended to a relative CSV path in the extract section.
        If the CSV path is already absolute, data_dir is ignored.
        """
        config = parse_yaml(yaml_text)

        # Resolve CSV path
        csv_path = config.extract.csv
        if not os.path.isabs(csv_path) and data_dir is not None:
            csv_path = os.path.join(data_dir, csv_path)

        # Instantiate transforms from registry
        transforms = []
        for step in config.transforms:
            op = step.op
            if op not in REGISTRY:
                raise ValueError(f"Unknown transform op: '{op}'")
            transform_cls = REGISTRY[op]

            if op == "filter":
                t = transform_cls(
                    column=step.column,
                    op_kind=step.op_kind,
                    value=step.value,
                )
            elif op == "rename":
                t = transform_cls(mapping=step.mapping)
            elif op == "derive":
                t = transform_cls(column=step.column, expr=step.expr)
            elif op == "aggregate":
                t = transform_cls(group_by=step.group_by, agg=step.agg)
            else:
                raise ValueError(f"Unknown transform op: '{op}'")
            transforms.append(t)

        # Create in-memory SQLite engine
        engine = create_engine("sqlite:///:memory:")

        return cls(
            csv_path=csv_path,
            transforms=transforms,
            table_name=config.load.table,
            engine=engine,
        )

    def _validate_upfront(self, df: pd.DataFrame, transforms) -> None:
        """Validate filter columns upfront (before any transforms are applied).

        Per spec: raise ValueError if a filter column is not present in the
        raw DataFrame. Rename source key and derive expr variable references
        are also validated here if they match existing column names.

        Aggregate validation happens at step time (inside Aggregate.apply()).
        """
        cols = set(df.columns)

        for t in transforms:
            from transforms import FilterRows, RenameColumns, DeriveColumn

            if isinstance(t, FilterRows):
                if t.column not in cols:
                    raise ValueError(
                        f"Pipeline: filter column '{t.column}' not found in DataFrame. "
                        f"Available columns: {sorted(cols)}"
                    )
            elif isinstance(t, RenameColumns):
                # Validate rename source keys — warn if missing (spec says raise ValueError)
                for src_key in t.mapping:
                    if src_key not in cols:
                        raise ValueError(
                            f"Pipeline: rename source key '{src_key}' not found in DataFrame. "
                            f"Available columns: {sorted(cols)}"
                        )
            elif isinstance(t, DeriveColumn):
                # Validate expr variable references that match existing column names
                expr_tokens = _extract_expr_columns(t.expr)
                for token in expr_tokens:
                    if token in cols:
                        # Column reference found, it's valid
                        pass
                    # We don't raise for tokens that don't match columns —
                    # they could be numeric literals or built-in functions

    def run(self) -> pd.DataFrame:
        """Execute the full pipeline: extract → transform → load → return.

        Reads the CSV, applies each transform in order, loads the final
        DataFrame into the SQLAlchemy table, and returns the final DataFrame.

        Raises ValueError if a column required by a transform step is missing
        from the DataFrame at the point where that step is applied.
        """
        # Extract
        df = pd.read_csv(self._csv_path)

        # Upfront validation (filter columns on raw df, rename source keys, derive vars)
        self._validate_upfront(df, self._transforms)

        # Apply transforms in order (each handles its own step-time validation)
        for t in self._transforms:
            df = t.apply(df)

        # Load
        loader = SQLAlchemyLoader(self._table_name, self.engine)
        loader.load(df)

        self._ran = True
        return df

    def query(self, sql: str) -> List[dict]:
        """Execute a raw SQL string against the loaded table.

        Returns a list of row dicts (column name → Python value).
        Raises RuntimeError if run() has not been called first.
        """
        if not self._ran:
            raise RuntimeError(
                "Pipeline.query() called before Pipeline.run(). "
                "Call run() first to populate the database."
            )
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result]
