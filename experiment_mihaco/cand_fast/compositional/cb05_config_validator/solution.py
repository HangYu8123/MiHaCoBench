import yaml
import re
import json
import hashlib


def validate_config(yaml_text: str, schema: dict) -> dict:
    """
    Parse yaml_text, validate against schema, and return the validated config
    with an added '_hash' key containing the SHA-256 fingerprint.
    """
    # Step 1: Parse YAML
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        raise ValueError("Failed to parse YAML text")

    if not isinstance(parsed, dict):
        raise ValueError("YAML content must be a mapping (dict)")

    validated = {}

    # Step 2 & 3: Iterate schema keys in sorted order and build validated dict
    for key in sorted(schema):
        rule = schema[key]
        required = rule.get("required", False)

        if key not in parsed:
            # Key is absent
            if required:
                raise KeyError(key)
            elif "default" in rule:
                # Fill with default without type-checking
                validated[key] = rule["default"]
            # else: skip key entirely
        else:
            value = parsed[key]
            expected_type = rule["type"]

            # Type check (TypeError)
            type_ok = False
            if expected_type == "bool":
                type_ok = isinstance(value, bool)
            elif expected_type == "int":
                type_ok = isinstance(value, int) and not isinstance(value, bool)
            elif expected_type == "float":
                type_ok = isinstance(value, (int, float)) and not isinstance(value, bool)
            elif expected_type == "str":
                type_ok = isinstance(value, str)
            elif expected_type == "list":
                type_ok = isinstance(value, list)

            if not type_ok:
                raise TypeError(
                    f"Key '{key}': expected type '{expected_type}', got {type(value).__name__}"
                )

            # Constraint checks (ValueError)
            if expected_type == "str" and "pattern" in rule:
                if re.search(rule["pattern"], value) is None:
                    raise ValueError(
                        f"Key '{key}': value {value!r} does not match pattern {rule['pattern']!r}"
                    )

            if expected_type in ("int", "float"):
                if "min" in rule and value < rule["min"]:
                    raise ValueError(
                        f"Key '{key}': value {value} is below minimum {rule['min']}"
                    )
                if "max" in rule and value > rule["max"]:
                    raise ValueError(
                        f"Key '{key}': value {value} is above maximum {rule['max']}"
                    )

            validated[key] = value

    # Step 4: Compute hash BEFORE adding "_hash"
    canonical = json.dumps(validated, sort_keys=True, separators=(",", ":"))
    _hash = hashlib.sha256(canonical.encode()).hexdigest()

    # Step 5: Return validated dict with "_hash" appended
    return {**validated, "_hash": _hash}
