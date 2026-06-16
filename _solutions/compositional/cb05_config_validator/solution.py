"""Gold reference for compositional/cb05_config_validator.

A YAML config validator with a canonical SHA-256 fingerprint. Composes four
libraries:

* ``yaml`` (PyYAML, ``yaml.safe_load``) — parse the YAML text,
* ``re``     — regex ``pattern`` constraints for string fields,
* ``json``   — canonical serialization of the validated config,
* ``hashlib``— SHA-256 of the canonical bytes.

The exception precedence (per key) is exactly:
    required-presence (KeyError) > type (TypeError) > constraint (ValueError).
"""
from __future__ import annotations

import hashlib
import json
import re

import yaml

# Python types accepted for each schema "type". bool is intentionally excluded
# from the numeric types (a bool is NOT an int here).
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

    Parameters
    ----------
    yaml_text : str
        The YAML document.
    schema : dict
        Maps key name -> rule dict. A rule may contain ``type`` (required, one
        of int/float/str/bool/list), ``required`` (bool, default False),
        ``default``, ``pattern`` (regex string, for str), and numeric
        ``min``/``max`` bounds (for int/float).

    Returns
    -------
    dict
        The validated key/value pairs plus an added ``"_hash"`` key whose value
        is the SHA-256 hex digest of the canonical JSON of the validated dict
        (computed before ``"_hash"`` is added).

    Raises
    ------
    ValueError
        If ``yaml.safe_load`` fails, the parsed object is not a mapping, a
        string fails its ``pattern``, or a number is outside ``[min, max]``.
    KeyError
        If a required key is absent (and has no usable default). Checked before
        any type or constraint check.
    TypeError
        If a present value's Python type does not match the rule ``type``.
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
        value = parsed[key] if present else _MISSING

        # 1. required-presence (KeyError) — happens BEFORE type/constraint.
        if not present:
            if rule.get("required", False):
                raise KeyError(key)
            if "default" in rule:
                # default is filled WITHOUT type-checking.
                validated[key] = rule["default"]
            continue

        # 2. type (TypeError).
        check = _TYPE_CHECKS[rule_type]
        if not check(value):
            raise TypeError(
                f"key {key!r}: expected {rule_type}, got {type(value).__name__}"
            )

        # 3. constraints (ValueError).
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
