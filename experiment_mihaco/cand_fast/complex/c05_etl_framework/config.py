"""config.py — Parse a YAML pipeline spec into dataclasses."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractConfig:
    csv: str


@dataclass
class TransformStep:
    op: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadConfig:
    table: str


@dataclass
class PipelineConfig:
    extract: ExtractConfig
    transforms: list[TransformStep]
    load: LoadConfig


def parse_config(yaml_text: str) -> PipelineConfig:
    """Parse YAML text into a PipelineConfig dataclass."""
    cfg = yaml.safe_load(yaml_text)

    extract = ExtractConfig(csv=cfg["extract"]["csv"])

    transforms = []
    for step in cfg.get("transforms", []):
        op = step["op"]
        params = {k: v for k, v in step.items() if k != "op"}
        transforms.append(TransformStep(op=op, params=params))

    load = LoadConfig(table=cfg["load"]["table"])

    return PipelineConfig(extract=extract, transforms=transforms, load=load)
