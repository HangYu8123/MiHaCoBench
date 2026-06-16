"""Grader for easy/e06_semver_order. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "easy", "e06_semver_order"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
parse = gu.load_callable(SOL, "solution.py", "parse")
compare = gu.load_callable(SOL, "solution.py", "compare")
sort_versions = gu.load_callable(SOL, "solution.py", "sort_versions")


# --------------------------------------------------------------------------- #
# PASS_TO_PASS — true on both gold and broken
# --------------------------------------------------------------------------- #
def test_parse_basic_fields():
    p = parse("1.2.3-alpha.1+build.7")
    assert p["major"] == 1
    assert p["minor"] == 2
    assert p["patch"] == 3
    assert p["prerelease"] == ["alpha", "1"]
    assert p["build"] == ["build", "7"]


def test_parse_plain_version_has_empty_pre_and_build():
    p = parse("0.0.0")
    assert p["prerelease"] == []
    assert p["build"] == []


def test_core_numeric_ordering():
    # 1.0.0 < 1.0.1 < 1.1.0 < 2.0.0
    assert compare("1.0.0", "1.0.1") == -1
    assert compare("1.0.1", "1.1.0") == -1
    assert compare("1.1.0", "2.0.0") == -1
    assert compare("2.0.0", "1.1.0") == 1


def test_prerelease_lower_than_release():
    assert compare("1.0.0-alpha", "1.0.0") == -1
    assert compare("1.0.0", "1.0.0-alpha") == 1


def test_build_metadata_ignored():
    assert compare("1.0.0+x", "1.0.0") == 0
    assert compare("1.0.0+build1", "1.0.0+build2") == 0


def test_equal_versions_compare_zero():
    assert compare("1.2.3-beta.2", "1.2.3-beta.2") == 0
    assert compare("0.0.1", "0.0.1") == 0


def test_parse_rejects_malformed():
    for bad in ["1.0", "1", "1.x.0", "1.0.beta", "1..0", "1.0.0-", "1.0.0-alpha..1", "1.0.0+"]:
        with pytest.raises(ValueError):
            parse(bad)


def test_cli_compare_path():
    proc = gu.run_cli(SOL, ["compare", "1.0.0", "1.0.1"], timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "-1"
    proc2 = gu.run_cli(SOL, ["compare", "2.0.0", "1.0.0"], timeout=30)
    assert proc2.returncode == 0, proc2.stderr
    assert proc2.stdout.strip() == "1"


def test_cli_malformed_errors():
    proc = gu.run_cli(SOL, ["compare", "1.0", "1.0.0"], timeout=30)
    assert proc.returncode != 0


# --------------------------------------------------------------------------- #
# FAIL_TO_PASS — true on gold, false on broken (numeric pre-release handling)
# --------------------------------------------------------------------------- #
def test_numeric_prerelease_identifier_ordering():
    # alpha.9 < alpha.11 numerically (broken compares "9" > "11" lexically → +1)
    assert compare("1.0.0-alpha.9", "1.0.0-alpha.11") == -1
    assert compare("1.0.0-alpha.11", "1.0.0-alpha.9") == 1


def test_sort_places_numeric_identifiers_in_numeric_order():
    out = sort_versions(["1.0.0-alpha.10", "1.0.0-alpha.2"])
    assert out == ["1.0.0-alpha.2", "1.0.0-alpha.10"]


def test_numeric_identifier_below_alphanumeric():
    # A purely numeric identifier has LOWER precedence than an alphanumeric one.
    assert compare("1.0.0-1", "1.0.0-alpha") == -1
    assert compare("1.0.0-alpha", "1.0.0-1") == 1
    # Chosen so a raw-string compare would invert the answer: numeric "2" sorts
    # AFTER alphanumeric "1alpha" lexically (0x32 > 0x31) but is lower precedence.
    assert compare("1.0.0-2", "1.0.0-1alpha") == -1
    assert compare("1.0.0-1alpha", "1.0.0-2") == 1


def test_more_identifiers_higher_when_prefix_equal():
    assert compare("1.0.0-alpha", "1.0.0-alpha.1") == -1
    assert compare("1.0.0-alpha.1", "1.0.0-alpha") == 1


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
