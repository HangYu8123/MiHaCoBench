"""config.py — Parse a YAML pipeline spec into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ExtractConfig:
    csv: str


@dataclass
class TransformStep:
    op: str
    column: Optional[str] = None
    op_kind: Optional[str] = None
    value: Any = None
    mapping: Optional[Dict[str, str]] = None
    expr: Optional[str] = None
    group_by: Optional[List[str]] = None
    agg: Optional[Dict[str, str]] = None


@dataclass
class LoadConfig:
    table: str


@dataclass
class PipelineConfig:
    extract: ExtractConfig
    transforms: List[TransformStep]
    load: LoadConfig


def parse_yaml(text: str) -> PipelineConfig:
    """Parse YAML text into a PipelineConfig dataclass."""
    data = yaml.safe_load(text)

    extract = ExtractConfig(csv=data["extract"]["csv"])

    transforms = []
    for step in data.get("transforms", []):
        transforms.append(TransformStep(**step))

    load = LoadConfig(table=data["load"]["table"])

    return PipelineConfig(extract=extract, transforms=transforms, load=load)
