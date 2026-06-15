"""Grader for easy/e02_ini_parser. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "easy", "e02_ini_parser"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
parse_ini = gu.load_callable(SOL, "solution.py", "parse_ini")


# ---------------------------------------------------------------------------
# Test 1: sections and keys are detected correctly
# ---------------------------------------------------------------------------
def test_sections_and_keys():
    text = """
[alpha]
foo = bar
baz = qux

[beta]
x = 1
"""
    result = parse_ini(text)
    assert set(result) == {"alpha", "beta"}
    assert set(result["alpha"]) == {"foo", "baz"}
    assert set(result["beta"]) == {"x"}


# ---------------------------------------------------------------------------
# Test 2: both separators (= and :) are accepted
# ---------------------------------------------------------------------------
def test_both_separators():
    text = """
[sec]
key1 = value1
key2: value2
"""
    result = parse_ini(text)
    assert result["sec"]["key1"] == "value1"
    assert result["sec"]["key2"] == "value2"


# ---------------------------------------------------------------------------
# Test 3: comments and blank lines are ignored
# ---------------------------------------------------------------------------
def test_comments_and_blanks_ignored():
    text = """
# this is a comment
; so is this

[section]
# another comment
a = 1

; inline comment line
b = 2
"""
    result = parse_ini(text)
    assert set(result["section"]) == {"a", "b"}
    assert result["section"]["a"] == 1
    assert result["section"]["b"] == 2


# ---------------------------------------------------------------------------
# Test 4: keys before any section go into "default"
# ---------------------------------------------------------------------------
def test_default_section():
    text = """
orphan = hello
another = world

[actual]
key = val
"""
    result = parse_ini(text)
    assert "default" in result
    assert result["default"]["orphan"] == "hello"
    assert result["default"]["another"] == "world"
    assert result["actual"]["key"] == "val"


# ---------------------------------------------------------------------------
# Test 5: duplicate key — last value wins
# ---------------------------------------------------------------------------
def test_duplicate_key_last_wins():
    text = """
[sec]
key = first
key = second
key = third
"""
    result = parse_ini(text)
    assert result["sec"]["key"] == "third"


# ---------------------------------------------------------------------------
# Test 6: value coercion — int, float, bool (true/false/yes/no), str
# ---------------------------------------------------------------------------
def test_coercion_int():
    text = "[s]\ncount = 42\nneg = -7\n"
    result = parse_ini(text)
    assert result["s"]["count"] == 42
    assert isinstance(result["s"]["count"], int)
    assert result["s"]["neg"] == -7
    assert isinstance(result["s"]["neg"], int)


def test_coercion_float():
    text = "[s]\nratio = 3.14\ntemp = -0.5\n"
    result = parse_ini(text)
    assert gu.close(result["s"]["ratio"], 3.14)
    assert isinstance(result["s"]["ratio"], float)
    assert gu.close(result["s"]["temp"], -0.5)


def test_coercion_bool_true_yes():
    text = "[s]\nflag1 = true\nflag2 = True\nflag3 = yes\nflag4 = YES\n"
    result = parse_ini(text)
    assert result["s"]["flag1"] is True
    assert result["s"]["flag2"] is True
    assert result["s"]["flag3"] is True
    assert result["s"]["flag4"] is True


def test_coercion_bool_false_no():
    text = "[s]\nflag1 = false\nflag2 = False\nflag3 = no\nflag4 = NO\n"
    result = parse_ini(text)
    assert result["s"]["flag1"] is False
    assert result["s"]["flag2"] is False
    assert result["s"]["flag3"] is False   # broken variant leaves "no" as str
    assert result["s"]["flag4"] is False


def test_coercion_str():
    text = "[s]\nname = hello world\npath = /usr/bin\n"
    result = parse_ini(text)
    assert result["s"]["name"] == "hello world"
    assert result["s"]["path"] == "/usr/bin"


# ---------------------------------------------------------------------------
# Test 7: interpolation — success
# ---------------------------------------------------------------------------
def test_interpolation_success():
    text = """
[server]
host = localhost
port = 8080

[database]
host = ${server.host}
url = http://${server.host}:${server.port}/db
"""
    result = parse_ini(text)
    assert result["database"]["host"] == "localhost"
    assert result["database"]["url"] == "http://localhost:8080/db"


def test_interpolation_chained():
    """Interpolation result itself contains another reference (multi-hop)."""
    text = """
[a]
x = hello

[b]
y = ${a.x}

[c]
z = ${b.y} world
"""
    result = parse_ini(text)
    assert result["c"]["z"] == "hello world"


# ---------------------------------------------------------------------------
# Test 8: interpolation — missing reference raises ValueError
# ---------------------------------------------------------------------------
def test_interpolation_missing_section_raises():
    text = """
[sec]
val = ${nonexistent.key}
"""
    with pytest.raises(ValueError):
        parse_ini(text)


def test_interpolation_missing_key_raises():
    text = """
[alpha]
x = 1

[beta]
y = ${alpha.z}
"""
    with pytest.raises(ValueError):
        parse_ini(text)


# ---------------------------------------------------------------------------
# Test 9: interpolation — cycle raises ValueError
# ---------------------------------------------------------------------------
def test_interpolation_cycle_raises():
    text = """
[x]
a = ${x.b}
b = ${x.a}
"""
    with pytest.raises(ValueError):
        parse_ini(text)


# ---------------------------------------------------------------------------
# Test 10: empty input returns empty dict (edge case)
# ---------------------------------------------------------------------------
def test_empty_input():
    assert parse_ini("") == {}


# ---------------------------------------------------------------------------
# Test 11: whitespace stripping in keys, values, section names
# ---------------------------------------------------------------------------
def test_whitespace_stripping():
    text = "[ my section ]\n  key  =   value  \n"
    result = parse_ini(text)
    assert "my section" in result
    assert result["my section"]["key"] == "value"


# ---------------------------------------------------------------------------
# Advisory code quality report (never asserted)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
