"""
config.py — Parse a YAML pipeline spec into dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import yaml


@dataclass
class ExtractConfig:
    csv: str


@dataclass
class LoadConfig:
    table: str


@dataclass
class FilterTransformConfig:
    op: str  # "filter"
    column: str
    op_kind: str
    value: Any


@dataclass
class RenameTransformConfig:
    op: str  # "rename"
    mapping: Dict[str, str]


@dataclass
class DeriveTransformConfig:
    op: str  # "derive"
    column: str
    expr: str


@dataclass
class AggregateTransformConfig:
    op: str  # "aggregate"
    group_by: List[str]
    agg: Dict[str, str]


TransformConfig = Union[
    FilterTransformConfig,
    RenameTransformConfig,
    DeriveTransformConfig,
    AggregateTransformConfig,
]


@dataclass
class PipelineConfig:
    extract: ExtractConfig
    transforms: List[TransformConfig]
    load: LoadConfig


def parse_transform(raw: dict) -> TransformConfig:
    """Parse a single transform dict into the appropriate config dataclass."""
    op = raw["op"]
    if op == "filter":
        return FilterTransformConfig(
            op=op,
            column=raw["column"],
            op_kind=raw["op_kind"],
            value=raw["value"],
        )
    elif op == "rename":
        return RenameTransformConfig(
            op=op,
            mapping=dict(raw["mapping"]),
        )
    elif op == "derive":
        return DeriveTransformConfig(
            op=op,
            column=raw["column"],
            expr=raw["expr"],
        )
    elif op == "aggregate":
        return AggregateTransformConfig(
            op=op,
            group_by=list(raw["group_by"]),
            agg=dict(raw["agg"]),
        )
    else:
        raise ValueError(f"Unknown transform op: {op!r}")


def parse_pipeline_config(yaml_text: str) -> PipelineConfig:
    """Parse a YAML pipeline spec string into a PipelineConfig."""
    raw = yaml.safe_load(yaml_text)

    extract = ExtractConfig(csv=raw["extract"]["csv"])
    load = LoadConfig(table=raw["load"]["table"])

    transforms = []
    for t in raw.get("transforms", []):
        transforms.append(parse_transform(t))

    return PipelineConfig(
        extract=extract,
        transforms=transforms,
        load=load,
    )
