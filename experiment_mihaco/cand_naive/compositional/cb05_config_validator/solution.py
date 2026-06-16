"""
Compositional 05 — config_validator: YAML Config Validator with Canonical Hashing
"""

import hashlib
import json
import re

import yaml


def validate_config(yaml_text: str, schema: dict) -> dict:
    """
    Parse yaml_text with yaml.safe_load, validate the resulting mapping against
    schema, and return a new dict containing the validated key/value pairs plus
    an added "_hash" key.
    """
    # Step 1: Parse YAML
    try:
        parsed = yaml.safe_load(yaml_text)
    except Exception:
        raise ValueError("yaml.safe_load failed to parse the YAML text")

    if not isinstance(parsed, dict):
        raise ValueError("Parsed YAML is not a mapping (dict)")

    # Step 3: Build validated dict by iterating schema keys in sorted order
    validated = {}

    for key in sorted(schema):
        rule = schema[key]
        required = rule.get("required", False)
        expected_type = rule["type"]
        has_default = "default" in rule
        default_value = rule.get("default")

        if key in parsed:
            value = parsed[key]

            # Type check (before constraint check, after presence check)
            if not _check_type(value, expected_type):
                raise TypeError(
                    f"Key '{key}': expected type '{expected_type}', "
                    f"got {type(value).__name__}"
                )

            # Constraint checks
            if expected_type == "str" and "pattern" in rule:
                pattern = rule["pattern"]
                if re.search(pattern, value) is None:
                    raise ValueError(
                        f"Key '{key}': value {value!r} does not match pattern {pattern!r}"
                    )

            if expected_type in ("int", "float"):
                if "min" in rule and value < rule["min"]:
                    raise ValueError(
                        f"Key '{key}': value {value} is below min {rule['min']}"
                    )
                if "max" in rule and value > rule["max"]:
                    raise ValueError(
                        f"Key '{key}': value {value} is above max {rule['max']}"
                    )

            validated[key] = value

        else:
            # Key is absent
            if required:
                raise KeyError(key)
            elif has_default:
                validated[key] = default_value
            # If not required and no default, key is simply omitted

    # Step 4: Compute hash over validated dict (before adding _hash)
    canonical = json.dumps(validated, sort_keys=True, separators=(",", ":"))
    _hash = hashlib.sha256(canonical.encode()).hexdigest()

    # Step 5: Return validated with _hash added
    validated["_hash"] = _hash
    return validated


def _check_type(value, expected_type: str) -> bool:
    """
    Check if value's Python type matches the expected_type rule.

    | type    | accepted Python type                  |
    |---------|---------------------------------------|
    | "int"   | int but not bool                      |
    | "float" | float or int (but not bool)           |
    | "str"   | str                                   |
    | "bool"  | bool                                  |
    | "list"  | list                                  |
    """
    if expected_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "float":
        return isinstance(value, (float, int)) and not isinstance(value, bool)
    elif expected_type == "str":
        return isinstance(value, str)
    elif expected_type == "bool":
        return isinstance(value, bool)
    elif expected_type == "list":
        return isinstance(value, list)
    return False
