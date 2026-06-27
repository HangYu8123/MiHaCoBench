"""
Compositional 05 — config_validator
YAML Config Validator with Canonical SHA-256 Hashing.
"""

import hashlib
import json
import re

import yaml


_TYPE_MAP = {
    "int": int,
    "float": (float, int),
    "str": str,
    "bool": bool,
    "list": list,
}


def validate_config(yaml_text: str, schema: dict) -> dict:
    """Parse *yaml_text*, validate against *schema*, and return the validated
    mapping augmented with a ``"_hash"`` key (SHA-256 of the canonical JSON
    of the validated dict, computed before ``_hash`` is inserted).

    Raises
    ------
    ValueError
        If ``yaml.safe_load`` raises, the parsed value is not a ``dict``,
        a string value fails its ``pattern`` constraint, or a numeric value
        is outside ``[min, max]``.
    KeyError
        If a required key is absent (checked before any default substitution).
    TypeError
        If a present value's Python type does not match the rule ``type``.
    """
    # --- 1. Parse YAML ---
    try:
        data = yaml.safe_load(yaml_text)
    except Exception:
        raise ValueError("yaml.safe_load failed")

    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping (dict)")

    # --- 2. Validate each schema key in sorted order ---
    validated: dict = {}

    for key in sorted(schema):
        rule = schema[key]
        present = key in data

        # a) Required-presence check — highest precedence
        if rule.get("required", False) and not present:
            raise KeyError(key)

        # b) Default fill for absent optional keys
        if not present:
            if "default" in rule:
                validated[key] = rule["default"]
            # else: absent, no default — omit from validated
            continue

        # c) Key is present — retrieve value
        value = data[key]

        # d) Type check
        rule_type = rule.get("type")
        if rule_type is not None:
            # bool must be excluded for "int" and "float" (bool is subclass of int)
            if rule_type in ("int", "float") and type(value) is bool:
                raise TypeError(
                    f"Key '{key}': expected {rule_type}, got bool"
                )
            if rule_type == "int":
                if not isinstance(value, int):
                    raise TypeError(
                        f"Key '{key}': expected int, got {type(value).__name__}"
                    )
            elif rule_type == "float":
                if not isinstance(value, (float, int)):
                    raise TypeError(
                        f"Key '{key}': expected float or int, got {type(value).__name__}"
                    )
            elif rule_type == "str":
                if not isinstance(value, str):
                    raise TypeError(
                        f"Key '{key}': expected str, got {type(value).__name__}"
                    )
            elif rule_type == "bool":
                if not isinstance(value, bool):
                    raise TypeError(
                        f"Key '{key}': expected bool, got {type(value).__name__}"
                    )
            elif rule_type == "list":
                if not isinstance(value, list):
                    raise TypeError(
                        f"Key '{key}': expected list, got {type(value).__name__}"
                    )

        # e) Constraint checks — pattern first, then min/max
        if "pattern" in rule:
            if not isinstance(value, str) or re.search(rule["pattern"], value) is None:
                raise ValueError(
                    f"Key '{key}': value {value!r} does not match pattern {rule['pattern']!r}"
                )

        if "min" in rule:
            if value < rule["min"]:
                raise ValueError(
                    f"Key '{key}': value {value} is below minimum {rule['min']}"
                )

        if "max" in rule:
            if value > rule["max"]:
                raise ValueError(
                    f"Key '{key}': value {value} is above maximum {rule['max']}"
                )

        validated[key] = value

    # --- 3. Canonical SHA-256 hash (computed BEFORE adding _hash) ---
    _hash = hashlib.sha256(
        json.dumps(validated, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # --- 4. Return validated dict with _hash appended ---
    return validated | {"_hash": _hash}
