"""Grader for compositional/cb08_cursor_paginate.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference treats the cursor as INCLUSIVE (uses ``>=`` on the
(sort_key, id) boundary), so a full walk DUPLICATES the boundary row of every
page. The full-walk and tie-block tests catch this; the first-page,
single-page, and exception-path tests still pass on the broken variant.
"""
from __future__ import annotations

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb08_cursor_paginate"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

paginate = gu.load_callable(SOL, "solution.py", "paginate")


# ---------------------------------------------------------------------------
# Fixtures: deterministic DataFrames built inline (no committed data).
# ---------------------------------------------------------------------------
def _tie_df() -> pd.DataFrame:
    """A 9-row table whose score=10 tie block (ids 1,2,5,7) and score=20 tie
    block (ids 3,4) both straddle a page boundary at page_size=2/3.

    Rows below are listed deliberately OUT OF (score, id) order so a correct
    solution must sort; the canonical (score, id) order is:
        (10,1) (10,2) (10,5) (10,7) (20,3) (20,4) (30,6) (30,8) (40,9)
    """
    return pd.DataFrame(
        {
            "id":    [3, 1, 6, 2, 9, 5, 4, 8, 7],
            "score": [20, 10, 30, 10, 40, 10, 20, 30, 10],
            "name":  ["c", "a", "f", "b", "i", "e", "d", "h", "g"],
        }
    )


# Canonical (score, id) order of _tie_df(), used as the independent reference.
_CANON_ORDER = [
    (10, 1), (10, 2), (10, 5), (10, 7),
    (20, 3), (20, 4),
    (30, 6), (30, 8),
    (40, 9),
]


def _walk(df: pd.DataFrame, sort_key: str, page_size: int, max_calls: int = 1000):
    """Independent reference walk: drive paginate() from cursor=None until
    next_cursor is None, collecting every row's (sort_key, id) in arrival order.

    Returns (collected_pairs, n_pages). Guards against an infinite loop by
    capping the number of calls.
    """
    collected: list[tuple] = []
    pages = 0
    cursor = None
    while True:
        page = paginate(df, sort_key, page_size, cursor)
        pages += 1
        for r in page["rows"]:
            collected.append((r[sort_key], int(r["id"])))
        nxt = page["next_cursor"]
        if nxt is None:
            break
        cursor = nxt
        assert pages <= max_calls, "pagination did not terminate (possible non-None trailing cursor)"
    return collected, pages


# ---------------------------------------------------------------------------
# Test 1: return shape and keys
# ---------------------------------------------------------------------------
def test_return_shape_and_keys():
    df = _tie_df()
    page = paginate(df, "score", 3, None)
    assert isinstance(page, dict)
    assert set(page.keys()) == {"rows", "next_cursor"}
    assert isinstance(page["rows"], list)
    assert all(isinstance(r, dict) for r in page["rows"])
    assert page["next_cursor"] is None or isinstance(page["next_cursor"], str)


# ---------------------------------------------------------------------------
# Test 2: first page (cursor=None) returns the first page_size rows in order
# ---------------------------------------------------------------------------
def test_first_page_rows_and_cursor():
    df = _tie_df()
    page = paginate(df, "score", 3, None)
    got = [(r["score"], int(r["id"])) for r in page["rows"]]
    assert got == _CANON_ORDER[:3]
    # Full page with more rows remaining -> a non-None cursor.
    assert isinstance(page["next_cursor"], str)


# ---------------------------------------------------------------------------
# Test 3 [FAIL_TO_PASS]: a full walk yields EVERY row exactly once, in order,
# with NO duplicates and NO omissions. The inclusive-cursor bug duplicates the
# boundary row of each page, so the collected sequence differs from canonical.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("page_size", [1, 2, 3, 4])
def test_full_walk_no_dupes_no_gaps(page_size):
    df = _tie_df()
    collected, _pages = _walk(df, "score", page_size)
    assert collected == _CANON_ORDER, (
        f"page_size={page_size}: walk produced {collected}, expected {_CANON_ORDER}"
    )
    # Explicit no-duplicate guard (kills the inclusive-cursor defect directly).
    assert len(collected) == len(set(collected)) == len(_CANON_ORDER)


# ---------------------------------------------------------------------------
# Test 4 [FAIL_TO_PASS]: tie block straddling the boundary is paginated
# correctly. With page_size=2 the score=10 block (ids 1,2,5,7) spans two pages;
# the boundary row must not be repeated and the tied successor must not be skipped.
# ---------------------------------------------------------------------------
def test_tie_block_across_boundary():
    df = _tie_df()
    p1 = paginate(df, "score", 2, None)
    got1 = [(r["score"], int(r["id"])) for r in p1["rows"]]
    assert got1 == [(10, 1), (10, 2)]

    p2 = paginate(df, "score", 2, p1["next_cursor"])
    got2 = [(r["score"], int(r["id"])) for r in p2["rows"]]
    # (10,2) must NOT be repeated; (10,5) must NOT be skipped.
    assert got2 == [(10, 5), (10, 7)]


# ---------------------------------------------------------------------------
# Test 5 [FAIL_TO_PASS]: last page has next_cursor=None and there is no
# trailing empty page when page_size evenly divides the remaining rows.
# ---------------------------------------------------------------------------
def test_no_trailing_empty_page():
    # 4 rows, page_size=2: the second page is the final page and exactly fills
    # page_size, so its next_cursor MUST be None (no empty third page).
    df = pd.DataFrame({"id": [4, 1, 3, 2], "score": [10, 10, 20, 20]})
    p1 = paginate(df, "score", 2, None)
    assert [(r["score"], int(r["id"])) for r in p1["rows"]] == [(10, 1), (10, 4)]
    assert isinstance(p1["next_cursor"], str)

    p2 = paginate(df, "score", 2, p1["next_cursor"])
    assert [(r["score"], int(r["id"])) for r in p2["rows"]] == [(20, 2), (20, 3)]
    assert p2["next_cursor"] is None, "final full page must not leave a trailing empty page"


# ---------------------------------------------------------------------------
# Test 6: last partial page has next_cursor=None
# ---------------------------------------------------------------------------
def test_last_partial_page_cursor_none():
    df = _tie_df()  # 9 rows
    collected, pages = _walk(df, "score", 4)
    assert collected == _CANON_ORDER
    # 9 rows at page_size 4 -> pages of 4,4,1; the last page is partial.
    last = paginate(df, "score", 4, paginate(df, "score", 4, paginate(df, "score", 4, None)["next_cursor"])["next_cursor"])
    assert [(r["score"], int(r["id"])) for r in last["rows"]] == [(40, 9)]
    assert last["next_cursor"] is None


# ---------------------------------------------------------------------------
# Test 7: single page covering all rows -> next_cursor None
# ---------------------------------------------------------------------------
def test_single_page_covers_all():
    df = _tie_df()
    page = paginate(df, "score", 100, None)
    got = [(r["score"], int(r["id"])) for r in page["rows"]]
    assert got == _CANON_ORDER
    assert page["next_cursor"] is None


# ---------------------------------------------------------------------------
# Test 8: empty / singleton DataFrames
# ---------------------------------------------------------------------------
def test_empty_and_singleton():
    empty = pd.DataFrame({"id": pd.Series([], dtype="int64"),
                          "score": pd.Series([], dtype="int64")})
    page = paginate(empty, "score", 3, None)
    assert page["rows"] == []
    assert page["next_cursor"] is None

    single = pd.DataFrame({"id": [7], "score": [42]})
    page = paginate(single, "score", 3, None)
    assert [(r["score"], int(r["id"])) for r in page["rows"]] == [(42, 7)]
    assert page["next_cursor"] is None


# ---------------------------------------------------------------------------
# Test 9: string sort_key with ties is ordered (str ASC, id ASC)
# ---------------------------------------------------------------------------
def test_string_sort_key_with_ties():
    df = pd.DataFrame({
        "id":   [5, 2, 9, 1, 7],
        "name": ["b", "a", "b", "a", "b"],
    })
    # canonical order: (a,1) (a,2) (b,5) (b,7) (b,9)
    canon = [("a", 1), ("a", 2), ("b", 5), ("b", 7), ("b", 9)]
    collected = []
    cursor = None
    while True:
        page = paginate(df, "name", 2, cursor)
        collected += [(r["name"], int(r["id"])) for r in page["rows"]]
        if page["next_cursor"] is None:
            break
        cursor = page["next_cursor"]
    assert collected == canon
    assert len(collected) == len(set(collected))


# ---------------------------------------------------------------------------
# Test 10: malformed cursor token -> ValueError
# ---------------------------------------------------------------------------
def test_malformed_cursor_raises_valueerror():
    df = _tie_df()
    with pytest.raises(ValueError):
        paginate(df, "score", 2, "not-valid-base64-$$$")
    with pytest.raises(ValueError):
        paginate(df, "score", 2, "")
    # valid base64 but not the expected [value, id] json shape
    import base64 as _b64, json as _json
    bad = _b64.urlsafe_b64encode(_json.dumps({"a": 1}).encode()).decode()
    with pytest.raises(ValueError):
        paginate(df, "score", 2, bad)


# ---------------------------------------------------------------------------
# Test 11: page_size < 1 -> ValueError
# ---------------------------------------------------------------------------
def test_page_size_below_one_raises_valueerror():
    df = _tie_df()
    with pytest.raises(ValueError):
        paginate(df, "score", 0, None)
    with pytest.raises(ValueError):
        paginate(df, "score", -3, None)


# ---------------------------------------------------------------------------
# Test 12: missing id / missing sort_key column -> KeyError
# ---------------------------------------------------------------------------
def test_missing_columns_raise_keyerror():
    no_id = pd.DataFrame({"score": [1, 2, 3]})
    with pytest.raises(KeyError):
        paginate(no_id, "score", 2, None)

    no_key = pd.DataFrame({"id": [1, 2, 3], "score": [10, 20, 30]})
    with pytest.raises(KeyError):
        paginate(no_key, "missing_col", 2, None)


# ---------------------------------------------------------------------------
# Test 13: paginate is pure — it does not mutate the input DataFrame
# ---------------------------------------------------------------------------
def test_does_not_mutate_input():
    df = _tie_df()
    before = df.copy(deep=True)
    paginate(df, "score", 3, None)
    pd.testing.assert_frame_equal(df, before)


# ---------------------------------------------------------------------------
# Test 14: surface-form — must use pandas and base64
# ---------------------------------------------------------------------------
def test_source_uses_pandas_and_base64():
    usage = gu.source_uses(SOL, ["pandas", "base64", "sort_values"])
    assert usage["base64"], "solution.py must base64-encode the cursor token"
    assert usage["pandas"] or usage["sort_values"], (
        "solution.py must use pandas for the (sort_key, id) ordering"
    )


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
