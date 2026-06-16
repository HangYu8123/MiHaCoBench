"""BROKEN reference for compositional/cb05_config_validator.

PLANTED DEFECT (localized): the required-presence precedence is wrong. For a
MISSING key the code substitutes ``None`` (as if a default) and then falls
through to the type check, so a missing REQUIRED key raises TypeError (None is
not the rule type) instead of the contractually-required KeyError.

Concretely: the presence check no longer raises KeyError for required keys; it
only fills defaults / None, and the type check below then fires on the None.

Everything else (happy path, invalid-YAML ValueError, non-mapping ValueError,
wrong-type TypeError, pattern/range ValueError, bool-as-int TypeError, hashing)
remains correct.
"""
from __future__ import annotations

import hashlib
import json
import re

import yaml

_TYPE_CHECKS = {
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: (isinstance(v, float)
                        or (isinstance(v, int) and not isinstance(v, bool))),
    "str": lambda v: isinstance(v, str),
    "bool": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list),
}

_MISSING = object()


def validate_config(yaml_text: str, schema: dict) -> dict:
    """Parse ``yaml_text`` and validate it against ``schema``.

    See the gold reference / TASK.md for the full contract. This variant has a
    deliberately incorrect required-presence precedence.
    """
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("YAML document must be a mapping at the top level")

    validated: dict = {}

    for key in sorted(schema):
        rule = schema[key]
        rule_type = rule["type"]
        present = key in parsed

        # BUG: instead of raising KeyError for a missing required key, fill in
        # the default (or None) and fall through to the type check. The None
        # then fails the type check below -> TypeError, not KeyError.
        if not present:
            value = rule.get("default", None)
        else:
            value = parsed[key]

        # type (TypeError) — now also fires on a missing-required None.
        check = _TYPE_CHECKS[rule_type]
        if not check(value):
            raise TypeError(
                f"key {key!r}: expected {rule_type}, got {type(value).__name__}"
            )

        # constraints (ValueError).
        if rule_type == "str" and "pattern" in rule:
            if re.search(rule["pattern"], value) is None:
                raise ValueError(f"key {key!r}: value does not match pattern")

        if rule_type in ("int", "float"):
            if "min" in rule and value < rule["min"]:
                raise ValueError(f"key {key!r}: value below min")
            if "max" in rule and value > rule["max"]:
                raise ValueError(f"key {key!r}: value above max")

        validated[key] = value

    canonical = json.dumps(validated, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    validated["_hash"] = digest
    return validated
