"""config.py — Parse a YAML pipeline spec into dataclasses.

Each section of the YAML (extract, transforms, load) maps to a typed dataclass
so the rest of the framework never accesses raw dicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Extract config
# ---------------------------------------------------------------------------

@dataclass
class ExtractConfig:
    """Configuration for the extract (input) stage."""
    csv: str  # path to the CSV file (may be relative; resolved by Pipeline)


# ---------------------------------------------------------------------------
# Transform configs — one dataclass per op
# ---------------------------------------------------------------------------

@dataclass
class FilterConfig:
    """Keep only rows satisfying ``column op_kind value``."""
    column: str
    op_kind: str   # one of: ">", ">=", "<", "<=", "==", "!="
    value: Any     # cast to float if possible


@dataclass
class RenameConfig:
    """Rename columns according to a mapping dict."""
    mapping: dict[str, str]


@dataclass
class DeriveConfig:
    """Add a new column via ``df.eval(expr)``."""
    column: str
    expr: str


@dataclass
class AggregateConfig:
    """Group-by aggregation."""
    group_by: list[str]
    agg: dict[str, str]  # {column: func_name}


TransformConfig = FilterConfig | RenameConfig | DeriveConfig | AggregateConfig


# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------

@dataclass
class LoadConfig:
    """Configuration for the load (output) stage."""
    table: str  # SQLAlchemy table name


# ---------------------------------------------------------------------------
# Top-level pipeline config
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    """Full parsed pipeline specification."""
    extract: ExtractConfig
    transforms: list[TransformConfig] = field(default_factory=list)
    load: LoadConfig = field(default_factory=lambda: LoadConfig(table="output"))


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_transform(raw: dict) -> TransformConfig:
    """Parse a single transform dict from the YAML spec."""
    op = raw.get("op", "").lower()
    if op == "filter":
        return FilterConfig(
            column=raw["column"],
            op_kind=raw["op_kind"],
            value=raw["value"],
        )
    if op == "rename":
        return RenameConfig(mapping=dict(raw["mapping"]))
    if op == "derive":
        return DeriveConfig(column=raw["column"], expr=raw["expr"])
    if op == "aggregate":
        return AggregateConfig(
            group_by=list(raw["group_by"]),
            agg=dict(raw["agg"]),
        )
    raise ValueError(f"Unknown transform op: {op!r}")


def parse_yaml(yaml_text: str) -> PipelineConfig:
    """Parse a YAML pipeline spec string into a :class:`PipelineConfig`.

    Parameters
    ----------
    yaml_text:
        Raw YAML string (the full pipeline spec).

    Returns
    -------
    PipelineConfig
        Fully populated pipeline configuration.
    """
    raw = yaml.safe_load(yaml_text)

    # Extract
    extract_raw = raw.get("extract", {})
    extract = ExtractConfig(csv=str(extract_raw["csv"]))

    # Transforms
    transforms: list[TransformConfig] = []
    for t in raw.get("transforms", []):
        transforms.append(_parse_transform(t))

    # Load
    load_raw = raw.get("load", {})
    load = LoadConfig(table=str(load_raw.get("table", "output")))

    return PipelineConfig(extract=extract, transforms=transforms, load=load)
