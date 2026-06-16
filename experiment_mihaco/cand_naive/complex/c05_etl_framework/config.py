"""config.py — Parse a YAML pipeline spec into dataclasses."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class ExtractConfig:
    csv: str


@dataclass
class FilterConfig:
    column: str
    op_kind: str
    value: Any


@dataclass
class RenameConfig:
    mapping: dict[str, str]


@dataclass
class DeriveConfig:
    column: str
    expr: str


@dataclass
class AggregateConfig:
    group_by: list[str]
    agg: dict[str, str]


TransformConfig = FilterConfig | RenameConfig | DeriveConfig | AggregateConfig


@dataclass
class LoadConfig:
    table: str


@dataclass
class PipelineConfig:
    extract: ExtractConfig
    transforms: list[TransformConfig] = field(default_factory=list)
    load: LoadConfig = None


def parse_yaml(yaml_text: str, data_dir: str | None = None) -> PipelineConfig:
    """Parse YAML text into a PipelineConfig dataclass."""
    spec = yaml.safe_load(yaml_text)

    # Parse extract
    csv_path = spec["extract"]["csv"]
    if data_dir is not None and not os.path.isabs(csv_path):
        csv_path = os.path.join(data_dir, csv_path)
    extract = ExtractConfig(csv=csv_path)

    # Parse transforms
    transforms = []
    for t in spec.get("transforms", []):
        op = t["op"]
        if op == "filter":
            transforms.append(FilterConfig(
                column=t["column"],
                op_kind=t["op_kind"],
                value=t["value"],
            ))
        elif op == "rename":
            transforms.append(RenameConfig(mapping=dict(t["mapping"])))
        elif op == "derive":
            transforms.append(DeriveConfig(column=t["column"], expr=t["expr"]))
        elif op == "aggregate":
            transforms.append(AggregateConfig(
                group_by=list(t["group_by"]),
                agg=dict(t["agg"]),
            ))
        else:
            raise ValueError(f"Unknown transform op: {op!r}")

    # Parse load
    load = LoadConfig(table=spec["load"]["table"])

    return PipelineConfig(extract=extract, transforms=transforms, load=load)
