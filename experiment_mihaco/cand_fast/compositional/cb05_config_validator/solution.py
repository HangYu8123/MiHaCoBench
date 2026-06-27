"""
Compositional 05 — config_validator
YAML Config Validator with Canonical Hashing
"""

import hashlib
import json
import re

import yaml


def validate_config(yaml_text: str, schema: dict) -> dict:
    """
    Parse yaml_text with yaml.safe_load, validate the resulting mapping
    against schema, and return a new dict with validated key/value pairs
    plus an added "_hash" key.
    """
    # Step 1: Parse YAML; wrap any parse error as ValueError.
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValueError(str(exc)) from exc

    # Also raise ValueError if result is not a dict (e.g., None, list, scalar).
    if not isinstance(parsed, dict):
        raise ValueError(
            f"YAML document must be a mapping, got {type(parsed).__name__}"
        )

    # Step 2 & 3: Iterate schema keys in sorted order, build validated dict.
    validated = {}

    for key in sorted(schema):
        rule = schema[key]
        required = rule.get("required", False)
        has_default = "default" in rule
        field_type = rule.get("type")

        if key not in parsed:
            # Presence check: required takes absolute precedence over default.
            if required:
                raise KeyError(key)
            # Not required: use default if available, otherwise skip entirely.
            if has_default:
                validated[key] = rule["default"]
            # If not required and no default, key is omitted from validated.
            continue

        # Key is present — retrieve its value.
        value = parsed[key]

        # Type check (before constraint check, per precedence).
        if field_type is not None:
            type_ok = _check_type(value, field_type)
            if not type_ok:
                raise TypeError(
                    f"Key '{key}': expected type '{field_type}', "
                    f"got {type(value).__name__}"
                )

        # Constraint check.
        if field_type == "str":
            pattern = rule.get("pattern")
            if pattern is not None:
                if re.search(pattern, value) is None:
                    raise ValueError(
                        f"Key '{key}': value {value!r} does not match "
                        f"pattern {pattern!r}"
                    )
        elif field_type in ("int", "float"):
            if "min" in rule and value < rule["min"]:
                raise ValueError(
                    f"Key '{key}': value {value} is below minimum {rule['min']}"
                )
            if "max" in rule and value > rule["max"]:
                raise ValueError(
                    f"Key '{key}': value {value} is above maximum {rule['max']}"
                )

        validated[key] = value

    # Step 4: Compute SHA-256 hash over validated dict BEFORE adding "_hash".
    canonical = json.dumps(validated, sort_keys=True, separators=(",", ":"))
    hash_hex = hashlib.sha256(canonical.encode()).hexdigest()

    # Step 5: Add "_hash" and return.
    validated["_hash"] = hash_hex
    return validated


def _check_type(value, field_type: str) -> bool:
    """
    Return True if value matches the expected field_type.
    Handles the bool-subclass-of-int edge case explicitly.
    """
    if field_type == "int":
        # bool is a subclass of int; reject it explicitly.
        return isinstance(value, int) and not isinstance(value, bool)
    elif field_type == "float":
        # Accept int (but not bool) and float.
        return isinstance(value, (float, int)) and not isinstance(value, bool)
    elif field_type == "bool":
        return isinstance(value, bool)
    elif field_type == "str":
        return isinstance(value, str)
    elif field_type == "list":
        return isinstance(value, list)
    # Unknown type: pass through (no check).
    return True
