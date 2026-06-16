"""Grader for swe_bench/swe07_router_dispatch. Tests the public contract only (TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The symptom is observed via ``app.App.handle`` (app.py); the ROOT CAUSE lives in
``path.py`` (``split_path``). The broken variant strips only the LEADING slash and
keeps empty segments, so a path with a TRAILING slash gains a stray "" segment and
no longer matches a slash-free pattern of the intended length.

Tests:
  PASS_TO_PASS (gold AND broken agree):
    1. test_static_route_matches            — "/health" -> handler "health"
    2. test_single_param_no_slash           — "/users/5" -> id="5"
    3. test_two_param_extracts_both         — "/users/5/posts/9" -> uid, pid
    4. test_non_matching_path_returns_none  — unknown path -> handler None
    5. test_wrong_segment_count_returns_none— too many segments -> handler None
    6. test_root_routes_to_root_handler     — "/" -> registered root handler
    7. test_no_match_params_empty           — no-match result has params == {}

  FAIL_TO_PASS (gold true, broken false — trailing slash crosses the module boundary):
    8. test_trailing_slash_single_param     — "/users/5/" still -> id="5"
    9. test_trailing_slash_static_route     — "/health/" still -> handler "health"
   10. test_trailing_slash_two_param        — "/users/5/posts/9/" still extracts both

  Advisory:
   11. test_code_quality_report
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "swe_bench", "swe07_router_dispatch"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# The public entrypoint is the facade ``app.py`` (``from app import App``).
_app_mod = gu.load_module(SOL, "app.py", alias="app")
App = getattr(_app_mod, "App")


def _build_app():
    """Construct an App with a fixed, representative set of routes."""
    app = App()
    app.route("/", "home")
    app.route("/health", "health")
    app.route("/users/{id}", "show")
    app.route("/users/{uid}/posts/{pid}", "post")
    return app


# ===========================================================================
# PASS_TO_PASS — gold and broken both satisfy these
# ===========================================================================

def test_static_route_matches():
    """A static route matches with empty params."""
    app = _build_app()
    result = app.handle("/health")
    assert result["handler"] == "health", f"Got: {result}"
    assert result["params"] == {}, f"Got params: {result['params']}"


def test_single_param_no_slash():
    """A single-param route matches "/users/5" with id="5" (string)."""
    app = _build_app()
    result = app.handle("/users/5")
    assert result["handler"] == "show", f"Got: {result}"
    assert result["params"] == {"id": "5"}, f"Got params: {result['params']}"
    # Captured params are strings, not ints.
    assert isinstance(result["params"]["id"], str), "id must be captured as a str"


def test_two_param_extracts_both():
    """A two-param route extracts both captures."""
    app = _build_app()
    result = app.handle("/users/5/posts/9")
    assert result["handler"] == "post", f"Got: {result}"
    assert result["params"] == {"uid": "5", "pid": "9"}, f"Got params: {result['params']}"


def test_non_matching_path_returns_none():
    """A path with no registered route returns handler None and empty params."""
    app = _build_app()
    result = app.handle("/missing")
    assert result["handler"] is None, f"Expected no match, got: {result}"
    assert result["params"] == {}, f"Got params: {result['params']}"


def test_wrong_segment_count_returns_none():
    """A path with the wrong number of segments does not match a route."""
    app = _build_app()
    # "/users/{id}" has 2 segments; "/users/5/extra" has 3 -> no match.
    result = app.handle("/users/5/extra")
    assert result["handler"] is None, f"Expected no match, got: {result}"
    assert result["params"] == {}, f"Got params: {result['params']}"


def test_root_routes_to_root_handler():
    """The root path "/" routes to the registered root handler."""
    app = _build_app()
    result = app.handle("/")
    assert result["handler"] == "home", f"Got: {result}"
    assert result["params"] == {}, f"Got params: {result['params']}"


def test_no_match_params_empty():
    """No-match result is exactly {"handler": None, "params": {}}."""
    app = _build_app()
    result = app.handle("/totally/unknown/route")
    assert result == {"handler": None, "params": {}}, f"Got: {result}"


# ===========================================================================
# FAIL_TO_PASS — trailing-slash normalization (broken variant fails these)
# ===========================================================================

def test_trailing_slash_single_param():
    """A trailing slash is normalized away: "/users/5/" still matches id="5".

    GOLD strips both ends and drops empty segments, so "/users/5/" -> ["users","5"]
    matches the length-2 pattern. BROKEN strips only the leading slash and keeps the
    empty segment, so "/users/5/" -> ["users","5",""] (length 3) and returns None.
    """
    app = _build_app()
    result = app.handle("/users/5/")
    assert result["handler"] == "show", \
        f"Trailing slash should still match; got: {result}"
    assert result["params"] == {"id": "5"}, f"Got params: {result['params']}"


def test_trailing_slash_static_route():
    """A trailing slash on a static route still matches: "/health/" -> "health"."""
    app = _build_app()
    result = app.handle("/health/")
    assert result["handler"] == "health", \
        f"Trailing slash should still match; got: {result}"
    assert result["params"] == {}, f"Got params: {result['params']}"


def test_trailing_slash_two_param():
    """A trailing slash on a two-param route still extracts both captures."""
    app = _build_app()
    result = app.handle("/users/5/posts/9/")
    assert result["handler"] == "post", \
        f"Trailing slash should still match; got: {result}"
    assert result["params"] == {"uid": "5", "pid": "9"}, f"Got params: {result['params']}"


# ===========================================================================
# Advisory code quality
# ===========================================================================

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
