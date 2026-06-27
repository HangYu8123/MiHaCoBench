"""config.py — Parse YAML pipeline spec into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ExtractConfig:
    csv: str


@dataclass
class FilterConfig:
    op: str  # "filter"
    column: str
    op_kind: str  # ">", ">=", "<", "<=", "==", "!="
    value: Any


@dataclass
class RenameConfig:
    op: str  # "rename"
    mapping: Dict[str, str]


@dataclass
class DeriveConfig:
    op: str  # "derive"
    column: str
    expr: str


@dataclass
class AggregateConfig:
    op: str  # "aggregate"
    group_by: List[str]
    agg: Dict[str, str]


# Union type for transform configs
TransformConfig = FilterConfig | RenameConfig | DeriveConfig | AggregateConfig


@dataclass
class LoadConfig:
    table: str


@dataclass
class PipelineConfig:
    extract: ExtractConfig
    transforms: List[TransformConfig]
    load: LoadConfig


def _parse_transform(raw: dict) -> TransformConfig:
    """Dispatch on 'op' field to build the correct TransformConfig."""
    op = raw["op"]
    if op == "filter":
        return FilterConfig(
            op=op,
            column=raw["column"],
            op_kind=raw["op_kind"],
            value=raw["value"],
        )
    elif op == "rename":
        return RenameConfig(
            op=op,
            mapping=dict(raw["mapping"]),
        )
    elif op == "derive":
        return DeriveConfig(
            op=op,
            column=raw["column"],
            expr=raw["expr"],
        )
    elif op == "aggregate":
        return AggregateConfig(
            op=op,
            group_by=list(raw["group_by"]),
            agg=dict(raw["agg"]),
        )
    else:
        raise ValueError(f"Unknown transform op: {op!r}")


def parse_yaml(yaml_text: str) -> PipelineConfig:
    """Parse a YAML pipeline spec string into a PipelineConfig dataclass."""
    raw = yaml.safe_load(yaml_text)

    extract = ExtractConfig(csv=raw["extract"]["csv"])

    transforms = [_parse_transform(t) for t in (raw.get("transforms") or [])]

    load = LoadConfig(table=raw["load"]["table"])

    return PipelineConfig(extract=extract, transforms=transforms, load=load)
