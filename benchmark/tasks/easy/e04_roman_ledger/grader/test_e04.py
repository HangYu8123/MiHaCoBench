"""Grader for easy/e04_roman_ledger. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS >=1 test on the broken reference.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "easy", "e04_roman_ledger"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

to_roman   = gu.load_callable(SOL, "solution.py", "to_roman")
from_roman = gu.load_callable(SOL, "solution.py", "from_roman")
add_roman  = gu.load_callable(SOL, "solution.py", "add_roman")


# ---------------------------------------------------------------------------
# to_roman — known encodings (subtractive notation required)
# ---------------------------------------------------------------------------

def test_to_roman_subtractive_4():
    """4 must encode as 'IV', not 'IIII'."""
    assert to_roman(4) == "IV"


def test_to_roman_subtractive_9():
    """9 must encode as 'IX', not 'VIIII'."""
    assert to_roman(9) == "IX"


def test_to_roman_known_values():
    """Spot-check a variety of known subtractive-notation encodings."""
    cases = {
        1:    "I",
        3:    "III",
        4:    "IV",
        9:    "IX",
        14:   "XIV",
        40:   "XL",
        49:   "XLIX",
        90:   "XC",
        399:  "CCCXCIX",
        400:  "CD",
        499:  "CDXCIX",
        900:  "CM",
        1994: "MCMXCIV",
        2024: "MMXXIV",
        3999: "MMMCMXCIX",
    }
    for n, expected in cases.items():
        assert to_roman(n) == expected, f"to_roman({n}) expected {expected!r}"


def test_to_roman_boundary_min():
    assert to_roman(1) == "I"


def test_to_roman_boundary_max():
    assert to_roman(3999) == "MMMCMXCIX"


def test_to_roman_out_of_range_low():
    """to_roman(0) must raise ValueError."""
    with pytest.raises(ValueError):
        to_roman(0)


def test_to_roman_out_of_range_negative():
    """to_roman(-1) must raise ValueError."""
    with pytest.raises(ValueError):
        to_roman(-1)


def test_to_roman_out_of_range_high():
    """to_roman(4000) must raise ValueError."""
    with pytest.raises(ValueError):
        to_roman(4000)


# ---------------------------------------------------------------------------
# from_roman — known decodings and round-trip
# ---------------------------------------------------------------------------

def test_from_roman_known_values():
    """Decode a variety of canonical Roman strings."""
    cases = {
        "I":         1,
        "IV":        4,
        "IX":        9,
        "XIV":       14,
        "XL":        40,
        "XC":        90,
        "CD":        400,
        "CM":        900,
        "MCMXCIV":  1994,
        "MMXXIV":   2024,
        "MMMCMXCIX": 3999,
    }
    for s, expected in cases.items():
        assert from_roman(s) == expected, f"from_roman({s!r}) expected {expected}"


def test_round_trip_range():
    """to_roman(from_roman(s)) == s for all integers 1..3999."""
    for n in range(1, 4000):
        s = to_roman(n)
        assert from_roman(s) == n, f"round-trip failed for {n}: to_roman -> {s!r}"


def test_from_roman_malformed_iiii():
    """'IIII' is non-canonical — must raise ValueError."""
    with pytest.raises(ValueError):
        from_roman("IIII")


def test_from_roman_malformed_vv():
    """'VV' is non-canonical — must raise ValueError."""
    with pytest.raises(ValueError):
        from_roman("VV")


def test_from_roman_malformed_ic():
    """'IC' is non-canonical subtractive — must raise ValueError."""
    with pytest.raises(ValueError):
        from_roman("IC")


def test_from_roman_invalid_chars():
    """Strings with characters outside IVXLCDM must raise ValueError."""
    with pytest.raises(ValueError):
        from_roman("ABC")


def test_from_roman_empty_string():
    """Empty string must raise ValueError."""
    with pytest.raises(ValueError):
        from_roman("")


# ---------------------------------------------------------------------------
# add_roman
# ---------------------------------------------------------------------------

def test_add_roman_basic():
    """I + I = II."""
    assert add_roman("I", "I") == "II"


def test_add_roman_subtractive_result():
    """III + I = IV (subtractive notation in result)."""
    assert add_roman("III", "I") == "IV"


def test_add_roman_known():
    """XIV + XXVI = XL."""
    assert add_roman("XIV", "XXVI") == "XL"


def test_add_roman_large():
    """MCMXCIX + I = MM  (1999 + 1 = 2000)."""
    assert add_roman("MCMXCIX", "I") == "MM"


def test_add_roman_exceeds_3999():
    """Sum > 3999 must raise ValueError."""
    with pytest.raises(ValueError):
        add_roman("MMMCMXCIX", "I")   # 3999 + 1 = 4000


def test_add_roman_invalid_input():
    """Invalid Roman string as input must raise ValueError."""
    with pytest.raises(ValueError):
        add_roman("IIII", "I")


# ---------------------------------------------------------------------------
# Advisory code-quality report
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
