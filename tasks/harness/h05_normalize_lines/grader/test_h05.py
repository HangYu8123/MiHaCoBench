"""Grader for harness/h05_normalize_lines.

Tests the public contract only (see TASK.md): the single callable
``normalize(text, *, width, tabstop=4) -> list[str]``.

Validity invariant: PASSES on the gold reference (every test) and FAILS on the
broken reference (>=1 test). The broken reference implements every step except
width truncation correctly but, in the width step, counts every code point as
width 1 (ignoring East-Asian wide/fullwidth chars and zero-width combining
marks, with no grapheme protection). The FAIL_TO_PASS tests are exactly the
width-step tests that exercise wide / fullwidth / combining characters (the
ones marked ``FAIL_TO_PASS`` below); every other test, including the lone-``\\r``
line-split test, passes on the broken variant too (it implements steps 1-5
correctly) and serves as a correctness anchor.

Every expected output below is computed BY HAND from the rules in TASK.md,
independent of the gold implementation. All non-ASCII inputs use explicit
``\\u....`` escapes so the bytes under test are unambiguous.
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h05_normalize_lines"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

normalize = gu.load_callable(SOL, "solution.py", "normalize")


# Explicit code points used by the Unicode tests (documented for the reader):
#   漢 = CJK 'han'  (East-Asian Wide  -> column width 2)
#   字 = CJK 'zi'   (East-Asian Wide  -> column width 2)
#   Ａ = FULLWIDTH LATIN CAPITAL A (East-Asian Fullwidth -> column width 2)
#   ́ = COMBINING ACUTE ACCENT     (combining -> column width 0)
#   ̂ = COMBINING CIRCUMFLEX ACCENT(combining -> column width 0)
#   é = 'e' WITH ACUTE, precomposed (NFC of "e"+́; column width 1)
HAN = "漢"
ZI = "字"
FWA = "Ａ"


# ---------------------------------------------------------------------------
# Rule 1 — line splitting
# ---------------------------------------------------------------------------
def test_rule1_split_basic_and_interior_empty():
    # interior empty line preserved; no trailing empty line from final \n
    assert normalize("a\n\nb", width=80) == ["a", "", "b"]
    assert normalize("a\n", width=80) == ["a"]
    assert normalize("", width=80) == []


def test_rule1_crlf_is_single_separator():
    # "\r\n" counts as ONE separator (must NOT yield an empty line between).
    assert normalize("a\r\nb", width=80) == ["a", "b"]
    # mixed: trailing \n drops, interior \r\n stays single
    assert normalize("x\r\ny\r\n", width=80) == ["x", "y"]


def test_rule1_lone_cr_split():  # correctness (line splitting is correct in the broken variant)
    # A lone "\r" is its own separator.
    assert normalize("a\rb\rc\n", width=80) == ["a", "b", "c"]
    # combined separators in one string, per the TASK.md worked example
    assert normalize("a\r\nb\rc\n", width=80) == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Step 3 — tab expansion (true tabstop); tab-fill is NOT collapsed by step 2
# ---------------------------------------------------------------------------
def test_step3_tab_expansion_true_tabstop():
    assert normalize("a\tb", width=80) == ["a   b"]        # a@0, tab fills 1-3, b@4
    assert normalize("ab\tc", width=80) == ["ab  c"]       # ab@0-1, tab fills 2-3, c@4
    assert normalize("abc\td", width=80) == ["abc d"]      # abc@0-2, tab fills 3, d@4
    assert normalize("abcd\te", width=80) == ["abcd    e"]  # abcd@0-3, full tab to col 8


def test_step3_custom_tabstop():
    # tabstop=2: a@0, tab fills col 1, b@2
    assert normalize("a\tb", width=80, tabstop=2) == ["a b"]
    # tabstop=8: a@0, tab fills 1-7, b@8
    assert normalize("a\tb", width=80, tabstop=8) == ["a       b"]
    # leading tab is preserved (no leading collapse; fill is to a real column)
    assert normalize("\tx", width=80) == ["    x"]  # tab@0 fills cols 0-3, x@4


def test_collapse_runs_before_tab_expansion():
    # The input "  " before the tab collapses to a single space FIRST, which
    # shifts the tab's start column: "a  \tb" -> "a \tb" -> tab@col2 fills 2-3 -> "a   b".
    assert normalize("a  \tb", width=80) == ["a   b"]
    # A trailing tab's fill is stripped by step 4.
    assert normalize("a\t", width=80) == ["a"]


# ---------------------------------------------------------------------------
# Steps 2 & 4 — internal-space collapse (leading preserved) + trailing strip
# ---------------------------------------------------------------------------
def test_step2_internal_space_collapse():
    assert normalize("x  y   z", width=80) == ["x y z"]


def test_step2_4_leading_preserved_trailing_stripped():
    # leading 3 spaces kept exactly; internal run collapsed
    assert normalize("   indented  text", width=80) == ["   indented text"]
    # trailing spaces stripped (step 4)
    assert normalize("hello world   ", width=80) == ["hello world"]
    # a line of only spaces -> all leading, rest empty, then stripped -> ""
    assert normalize("     ", width=80) == [""]
    # leading + internal + trailing together
    assert normalize("  a   b  ", width=80) == ["  a b"]


# ---------------------------------------------------------------------------
# Step 5 — Unicode NFC
# ---------------------------------------------------------------------------
def test_step5_nfc_composition():
    # "e" + COMBINING ACUTE -> single precomposed code point U+00E9, so the
    # resulting line is exactly one code point long.
    out = normalize("é", width=80)
    assert out == ["é"]
    assert len(out[0]) == 1, "NFC must compose e+acute into one code point"


# ---------------------------------------------------------------------------
# Step 6 — width truncation, Unicode-aware
# ---------------------------------------------------------------------------
def test_step6_narrow_ascii_truncation():
    # all width-1 chars: plain prefix truncation
    assert normalize("abcdef", width=3) == ["abc"]
    assert normalize("abcdef", width=6) == ["abcdef"]
    assert normalize("abcdef", width=100) == ["abcdef"]


def test_step6_wide_cjk_truncation():  # FAIL_TO_PASS (kills all-width-1 defect)
    # "漢字ab" has column widths 2,2,1,1.
    s = HAN + ZI + "ab"
    # width=3: only HAN (2) fits; adding ZI would reach 4 > 3 -> stop.
    assert normalize(s, width=3) == [HAN]
    # width=4: HAN+ZI exactly fills 4; 'a' would reach 5 -> stop.
    assert normalize(s, width=4) == [HAN + ZI]
    # width=5: HAN+ZI+a fills 5; 'b' would reach 6 -> stop.
    assert normalize(s, width=5) == [HAN + ZI + "a"]
    # width=2: only HAN fits.
    assert normalize(s, width=2) == [HAN]
    # width=1: HAN (2) does not fit at all -> empty line.
    assert normalize(s, width=1) == [""]


def test_step6_fullwidth_counts_as_two():  # FAIL_TO_PASS (exercises the 'F' branch)
    # FULLWIDTH 'A' (U+FF21) is East-Asian *Fullwidth* -> column width 2.
    s = FWA + "z"
    assert normalize(s, width=1) == [""]        # fullwidth char (2) does not fit
    assert normalize(s, width=2) == [FWA]       # fits exactly; 'z' would reach 3
    assert normalize(s, width=3) == [FWA + "z"]  # both fit


def test_step6_nfc_then_truncate_composed():
    # "e"+COMBINING ACUTE + "xy" -> NFC "éxy" with widths 1,1,1.
    # width=2 -> first two code points. (Same on the broken variant since NFC
    # composes the accent away, so this is a correctness test, NOT FAIL_TO_PASS.)
    assert normalize("éxy", width=2) == ["éx"]
    assert normalize("éxy", width=1) == ["é"]


def test_step6_combining_marks_ride_along():  # FAIL_TO_PASS (width-0 + no-split)
    # "x"+COMBINING ACUTE+COMBINING CIRCUMFLEX+"yz": 'x' has no precomposed form
    # with these marks, so NFC keeps it decomposed. Column widths: 1,0,0,1,1.
    s = "x́̂yz"
    # width=1: base 'x' (1) fits; its two combining marks (width 0) ride along;
    # 'y' would reach 2 > 1 -> stop. Expected: x + both marks, nothing else.
    assert normalize(s, width=1) == ["x́̂"]
    # width=2: + 'y'
    assert normalize(s, width=2) == ["x́̂y"]
    # width=3 (and beyond): the whole line
    assert normalize(s, width=3) == ["x́̂yz"]
    assert normalize(s, width=50) == ["x́̂yz"]


def test_step6_no_split_drops_base_and_its_marks():  # FAIL_TO_PASS (width-0 marks)
    # "ab" + "x"+COMBINING ACUTE+COMBINING CIRCUMFLEX -> "abx́̂",
    # widths 1,1,1,0,0. width=2: 'a','b' fit (col 2); admitting base 'x' would
    # reach 3 > 2 -> stop BEFORE 'x', so its trailing marks are dropped too.
    s = "ab" + "x́̂"
    assert normalize(s, width=2) == ["ab"]
    # width=3: 'x' fits (col 3) and carries its marks; nothing after.
    assert normalize(s, width=3) == ["abx́̂"]


# ---------------------------------------------------------------------------
# Interaction: all rules together, multi-line
# ---------------------------------------------------------------------------
def test_interaction_all_rules_multiline():
    # Line A: "a\tb  c   "
    #   step 2 (collapse input spaces): "a\tb c   " -> "a\tb c " (the internal
    #     "  " before c collapses to " "; the trailing "   " collapses to " ")
    #   step 3 (expand tab): "a\tb c " -> "a   b c " (a@0, tab fills cols 1-3, b@4)
    #   step 4 (strip trailing): "a   b c " -> "a   b c"
    # Line B: "   keep  me" -> leading 3 spaces kept, internal "  " collapsed
    #   -> "   keep me".
    text = "a\tb  c   \n   keep  me"
    assert normalize(text, width=80) == ["a   b c", "   keep me"]


def test_interaction_collapse_before_width_and_wide():  # FAIL_TO_PASS (wide width)
    # "x   " + HAN + "  " + ZI : tab-free. Leading prefix empty.
    #   collapse internal runs: "x " + HAN + " " + ZI  -> "x 漢 字"
    #   widths: x=1, space=1, HAN=2, space=1, ZI=2  (cumulative 1,2,4,5,7)
    #   width=4 -> "x " (2) then HAN (->4) fits exactly; next space ->5 stop.
    s = "x   " + HAN + "  " + ZI
    assert normalize(s, width=4) == ["x " + HAN]
    # width=5 -> + the space after HAN (col 5); ZI would reach 7 -> stop.
    assert normalize(s, width=5) == ["x " + HAN + " "]


def test_interaction_per_line_independent_tabstops():
    # Tab stops reset at the start of EACH line (columns from col 0 per line).
    # No input spaces to collapse, so step 2 is a no-op and the tab-fill survives:
    #   line1: x@0, tab fills cols 1-3, y@4 => "x   y"
    #   line2: zz@0-1, tab fills cols 2-3, w@4 => "zz  w"
    text = "x\ty\nzz\tw"
    assert normalize(text, width=80) == ["x   y", "zz  w"]


# ---------------------------------------------------------------------------
# Exception contract — assert TYPES only
# ---------------------------------------------------------------------------
def test_width_below_one_raises_valueerror():
    with pytest.raises(ValueError):
        normalize("hello", width=0)
    with pytest.raises(ValueError):
        normalize("hello", width=-5)


def test_tabstop_below_one_raises_valueerror():
    with pytest.raises(ValueError):
        normalize("hello", width=80, tabstop=0)
    with pytest.raises(ValueError):
        normalize("hello", width=80, tabstop=-2)


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
