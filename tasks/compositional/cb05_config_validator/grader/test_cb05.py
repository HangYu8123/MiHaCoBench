"""Grader for compositional/cb05_config_validator.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference has the wrong required-presence precedence: a missing
REQUIRED key raises TypeError (None substituted, then type-checked) instead of
the contractual KeyError. The FAIL_TO_PASS test (``test_missing_required_raises_keyerror``)
discriminates gold from broken.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb05_config_validator"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

validate_config = gu.load_callable(SOL, "solution.py", "validate_config")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _expected_hash(validated_without_hash: dict) -> str:
    canonical = json.dumps(
        validated_without_hash, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Test 1: happy path — coercion, types, defaults applied, stable hash
# ---------------------------------------------------------------------------
def test_happy_path_values_and_hash():
    yaml_text = """
port: 8080
host: example.com
debug: true
tags:
  - a
  - b
"""
    schema = {
        "port": {"type": "int", "min": 1, "max": 65535},
        "host": {"type": "str", "pattern": r"^[a-z0-9.]+$"},
        "debug": {"type": "bool"},
        "tags": {"type": "list"},
        "retries": {"type": "int", "default": 3},  # absent -> default filled
    }
    result = validate_config(yaml_text, schema)
    assert isinstance(result, dict)

    # Coerced / passed-through values.
    assert result["port"] == 8080
    assert result["host"] == "example.com"
    assert result["debug"] is True
    assert result["tags"] == ["a", "b"]
    # Default filled for the absent, non-required key.
    assert result["retries"] == 3

    # Hash present and equal to sha256 of canonical JSON of the validated dict
    # WITHOUT the _hash key.
    assert "_hash" in result
    without_hash = {k: v for k, v in result.items() if k != "_hash"}
    assert result["_hash"] == _expected_hash(without_hash)


# ---------------------------------------------------------------------------
# Test 2: same input twice -> same hash; changed value -> different hash
# ---------------------------------------------------------------------------
def test_hash_stability_and_sensitivity():
    schema = {
        "port": {"type": "int"},
        "host": {"type": "str"},
    }
    yaml_a = "port: 80\nhost: a.com\n"
    yaml_b = "port: 81\nhost: a.com\n"  # one value changed

    h1 = validate_config(yaml_a, schema)["_hash"]
    h2 = validate_config(yaml_a, schema)["_hash"]
    h3 = validate_config(yaml_b, schema)["_hash"]

    assert h1 == h2, "same input must yield the same hash"
    assert h1 != h3, "changing a value must change the hash"
    assert isinstance(h1, str) and len(h1) == 64


# ---------------------------------------------------------------------------
# Test 3: invalid YAML -> ValueError
# ---------------------------------------------------------------------------
def test_invalid_yaml_raises_valueerror():
    # Unbalanced bracket / bad indentation -> yaml parse error.
    bad_yaml = "key: [1, 2, 3\nother: : :\n"
    schema = {"key": {"type": "list"}}
    with pytest.raises(ValueError):
        validate_config(bad_yaml, schema)


# ---------------------------------------------------------------------------
# Test 4: non-mapping YAML (top-level list) -> ValueError
# ---------------------------------------------------------------------------
def test_non_mapping_yaml_raises_valueerror():
    list_yaml = "- one\n- two\n- three\n"
    schema = {"anything": {"type": "str"}}
    with pytest.raises(ValueError):
        validate_config(list_yaml, schema)


# ---------------------------------------------------------------------------
# Test 5: wrong type -> TypeError
# ---------------------------------------------------------------------------
def test_wrong_type_raises_typeerror():
    yaml_text = "port: not_a_number\n"
    schema = {"port": {"type": "int"}}
    with pytest.raises(TypeError):
        validate_config(yaml_text, schema)


# ---------------------------------------------------------------------------
# Test 6: bool supplied where int expected -> TypeError
# ---------------------------------------------------------------------------
def test_bool_as_int_raises_typeerror():
    yaml_text = "count: true\n"
    schema = {"count": {"type": "int"}}
    with pytest.raises(TypeError):
        validate_config(yaml_text, schema)


# ---------------------------------------------------------------------------
# Test 7: pattern mismatch -> ValueError
# ---------------------------------------------------------------------------
def test_pattern_mismatch_raises_valueerror():
    yaml_text = "host: NOT-valid!!\n"
    schema = {"host": {"type": "str", "pattern": r"^[a-z0-9.]+$"}}
    with pytest.raises(ValueError):
        validate_config(yaml_text, schema)


# ---------------------------------------------------------------------------
# Test 8: out-of-range number -> ValueError
# ---------------------------------------------------------------------------
def test_out_of_range_raises_valueerror():
    yaml_text = "port: 70000\n"
    schema = {"port": {"type": "int", "min": 1, "max": 65535}}
    with pytest.raises(ValueError):
        validate_config(yaml_text, schema)


# ---------------------------------------------------------------------------
# Test 9 (FAIL_TO_PASS): missing REQUIRED key (no default) -> KeyError
# Gold raises KeyError (presence check precedes type check).
# Broken substitutes None then type-checks -> raises TypeError instead.
# ---------------------------------------------------------------------------
def test_missing_required_raises_keyerror():
    yaml_text = "host: example.com\n"  # 'port' absent
    schema = {
        "port": {"type": "int", "required": True},  # required, no default
        "host": {"type": "str"},
    }
    with pytest.raises(KeyError):
        validate_config(yaml_text, schema)


# ---------------------------------------------------------------------------
# Test 10: precedence — required missing key wins over a type problem elsewhere.
# A required key is absent AND another present key has a wrong type. Because
# keys are processed in sorted order and required-presence precedes type, the
# absent required 'aaa' must raise KeyError before the bad-typed 'zzz' is even
# reached. Gold: KeyError. Broken: 'aaa' None type-check fires first -> TypeError.
# ---------------------------------------------------------------------------
def test_precedence_required_before_type():
    yaml_text = "zzz: this_is_a_string\n"  # 'aaa' absent; 'zzz' is wrong type
    schema = {
        "aaa": {"type": "str", "required": True},  # absent, required, no default
        "zzz": {"type": "int"},                    # present but wrong type
    }
    with pytest.raises(KeyError):
        validate_config(yaml_text, schema)


# ---------------------------------------------------------------------------
# Test 11: float rule accepts an int value (and not a bool); range respected.
# ---------------------------------------------------------------------------
def test_float_accepts_int_value():
    yaml_text = "ratio: 5\n"  # YAML int, float rule should accept it
    schema = {"ratio": {"type": "float", "min": 0.0, "max": 10.0}}
    result = validate_config(yaml_text, schema)
    assert result["ratio"] == 5

    # bool where float expected is still a type error.
    with pytest.raises(TypeError):
        validate_config("ratio: true\n", {"ratio": {"type": "float"}})


# ---------------------------------------------------------------------------
# Test 12: surface-form — must use yaml.safe_load (never yaml.load)
# ---------------------------------------------------------------------------
def test_source_uses_safe_load():
    usage = gu.source_uses(SOL, ["yaml.safe_load", "hashlib"])
    assert usage["yaml.safe_load"], "solution.py must call yaml.safe_load"
    assert usage["hashlib"], "solution.py must use hashlib for the digest"
    unsafe = gu.source_uses(SOL, ["yaml.load("])
    assert not unsafe["yaml.load("], "must not use unsafe yaml.load("


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
