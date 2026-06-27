import yaml
import re
import json
import hashlib


def validate_config(yaml_text: str, schema: dict) -> dict:
    """
    Parse yaml_text with yaml.safe_load, validate against schema, and return
    the validated config dict with an added "_hash" key.
    """
    # Step 1: Parse YAML
    try:
        parsed = yaml.safe_load(yaml_text)
    except Exception:
        raise ValueError("yaml.safe_load failed to parse yaml_text")

    if not isinstance(parsed, dict):
        raise ValueError("Parsed YAML is not a mapping (dict)")

    # Step 2 & 3: Iterate schema keys in sorted order and build validated dict
    validated = {}

    for key in sorted(schema):
        rule = schema[key]
        required = rule.get("required", False)
        has_default = "default" in rule
        expected_type = rule["type"]

        if key not in parsed:
            # Key is absent
            if required:
                # Required and absent: raise KeyError (no default substitution)
                raise KeyError(key)
            elif has_default:
                # Not required, has default: fill with default (no type check)
                validated[key] = rule["default"]
            # else: not required, no default — skip (don't add to validated)
        else:
            # Key is present: check type first, then constraints
            value = parsed[key]

            # Type check
            type_ok = False
            if expected_type == "int":
                # int but not bool
                type_ok = isinstance(value, int) and not isinstance(value, bool)
            elif expected_type == "float":
                # float or int, but not bool
                type_ok = isinstance(value, (float, int)) and not isinstance(value, bool)
            elif expected_type == "str":
                type_ok = isinstance(value, str)
            elif expected_type == "bool":
                type_ok = isinstance(value, bool)
            elif expected_type == "list":
                type_ok = isinstance(value, list)

            if not type_ok:
                raise TypeError(
                    f"Key '{key}': expected type '{expected_type}', got {type(value).__name__}"
                )

            # Constraint checks (after type check)
            # pattern (only for str)
            if expected_type == "str" and "pattern" in rule:
                pattern = rule["pattern"]
                if re.search(pattern, value) is None:
                    raise ValueError(
                        f"Key '{key}': value {value!r} does not match pattern {pattern!r}"
                    )

            # min/max (for int or float)
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

    # Step 4: Compute hash over validated dict (before adding "_hash")
    canonical = json.dumps(validated, sort_keys=True, separators=(",", ":")).encode()
    _hash = hashlib.sha256(canonical).hexdigest()

    # Step 5: Return validated with added "_hash" key
    validated["_hash"] = _hash
    return validated
