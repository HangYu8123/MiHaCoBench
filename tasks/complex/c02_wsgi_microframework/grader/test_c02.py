"""Grader for complex/c02_wsgi_microframework.

Tests the public WSGI contract only — every test goes through the
WSGI callable returned by create_app().  No live server is started;
all requests are synthetic environ dicts.

Validity invariant: PASSES on the gold reference, FAILS on the __broken reference.
"""
from __future__ import annotations

import io
import json

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c02_wsgi_microframework"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the factory and build the app once for the whole session.
create_app = gu.load_callable(SOL, "app_factory.py", "create_app")
APP = create_app()


# --------------------------------------------------------------------------- #
# WSGI test helpers
# --------------------------------------------------------------------------- #

def _make_environ(
    method: str = "GET",
    path: str = "/",
    query_string: str = "",
    body: bytes = b"",
    content_type: str = "application/json",
) -> dict:
    """Build a minimal WSGI environ dict for testing."""
    environ: dict = {
        "REQUEST_METHOD": method.upper(),
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "wsgi.url_scheme": "http",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "HTTP_HOST": "localhost:8000",
    }
    return environ


def _call(environ: dict) -> tuple[str, list[tuple[str, str]], bytes]:
    """Call APP with *environ*.  Returns (status, headers, body_bytes)."""
    captured: dict = {}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers

    body_parts = APP(environ, start_response)
    body = b"".join(body_parts)
    return captured["status"], captured["headers"], body


def _status_code(status: str) -> int:
    return int(status.split(" ", 1)[0])


def _header(headers: list[tuple[str, str]], name: str) -> str | None:
    name_lower = name.lower()
    for k, v in headers:
        if k.lower() == name_lower:
            return v
    return None


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_get_root_200():
    """GET / returns 200."""
    env = _make_environ("GET", "/")
    status, headers, body = _call(env)
    assert _status_code(status) == 200, f"expected 200 got {status!r}"


def test_get_root_html_content_type():
    """GET / returns Content-Type: text/html (any charset ok)."""
    env = _make_environ("GET", "/")
    status, headers, body = _call(env)
    ct = _header(headers, "Content-Type") or ""
    assert "text/html" in ct.lower(), f"Content-Type was {ct!r}, expected text/html"


def test_get_root_contains_pybench():
    """GET / body contains the text 'PyBench' (jinja2-rendered)."""
    env = _make_environ("GET", "/")
    status, headers, body = _call(env)
    text = body.decode("utf-8", errors="replace")
    assert "PyBench" in text, f"'PyBench' not found in root response: {text[:200]!r}"


def test_get_hello_name():
    """GET /hello/<name> returns 200 JSON {"greeting": "Hello, <name>!"}."""
    env = _make_environ("GET", "/hello/World")
    status, headers, body = _call(env)
    assert _status_code(status) == 200, f"expected 200 got {status!r}"
    data = json.loads(body)
    assert data == {"greeting": "Hello, World!"}, f"unexpected body: {data!r}"


def test_get_hello_name_json_content_type():
    """GET /hello/<name> sets Content-Type: application/json."""
    env = _make_environ("GET", "/hello/Alice")
    status, headers, body = _call(env)
    ct = _header(headers, "Content-Type") or ""
    assert "application/json" in ct, f"Content-Type was {ct!r}"


def test_get_add_valid():
    """GET /add?a=3&b=4 returns 200 JSON {"sum": 7}."""
    env = _make_environ("GET", "/add", query_string="a=3&b=4")
    status, headers, body = _call(env)
    assert _status_code(status) == 200, f"expected 200 got {status!r}"
    data = json.loads(body)
    assert data == {"sum": 7}, f"unexpected body: {data!r}"


def test_get_add_negative_numbers():
    """GET /add?a=-5&b=10 returns {"sum": 5}."""
    env = _make_environ("GET", "/add", query_string="a=-5&b=10")
    status, headers, body = _call(env)
    assert _status_code(status) == 200, f"expected 200 got {status!r}"
    data = json.loads(body)
    assert data == {"sum": 5}, f"unexpected body: {data!r}"


def test_get_add_non_integer_returns_400():
    """GET /add?a=foo&b=3 returns 400 with JSON error."""
    env = _make_environ("GET", "/add", query_string="a=foo&b=3")
    status, headers, body = _call(env)
    assert _status_code(status) == 400, f"expected 400 got {status!r}"
    data = json.loads(body)
    assert "error" in data, f"expected 'error' key in {data!r}"


def test_get_add_float_returns_400():
    """GET /add?a=1.5&b=2 returns 400 (float is not int)."""
    env = _make_environ("GET", "/add", query_string="a=1.5&b=2")
    status, headers, body = _call(env)
    assert _status_code(status) == 400, f"expected 400 got {status!r}"


def test_post_echo():
    """POST /echo with JSON body returns 200 {"you_sent": <parsed>}."""
    payload = {"key": "value", "num": 42}
    body_bytes = json.dumps(payload).encode("utf-8")
    env = _make_environ("POST", "/echo", body=body_bytes)
    status, headers, body = _call(env)
    assert _status_code(status) == 200, f"expected 200 got {status!r}"
    data = json.loads(body)
    assert data == {"you_sent": payload}, f"unexpected body: {data!r}"


def test_post_echo_nested():
    """POST /echo echoes nested JSON faithfully."""
    payload = {"a": [1, 2, 3], "b": {"c": True}}
    body_bytes = json.dumps(payload).encode("utf-8")
    env = _make_environ("POST", "/echo", body=body_bytes)
    status, headers, body = _call(env)
    assert _status_code(status) == 200
    data = json.loads(body)
    assert data["you_sent"] == payload


def test_unknown_path_returns_404():
    """GET /nonexistent returns 404 JSON {"error": "not found"}."""
    env = _make_environ("GET", "/nonexistent")
    status, headers, body = _call(env)
    assert _status_code(status) == 404, f"expected 404 got {status!r}"
    data = json.loads(body)
    assert "error" in data, f"expected 'error' key in {data!r}"


def test_unknown_path_404_json_content_type():
    """404 response uses application/json Content-Type."""
    env = _make_environ("GET", "/no/such/path")
    status, headers, body = _call(env)
    assert _status_code(status) == 404
    ct = _header(headers, "Content-Type") or ""
    assert "application/json" in ct, f"expected application/json, got {ct!r}"


def test_wrong_method_returns_405():
    """POST / (GET-only route) returns 405."""
    env = _make_environ("POST", "/")
    status, headers, body = _call(env)
    assert _status_code(status) == 405, f"expected 405 got {status!r}"


def test_wrong_method_405_has_error_json():
    """405 response body is JSON with 'error' key."""
    env = _make_environ("DELETE", "/hello/test")
    status, headers, body = _call(env)
    assert _status_code(status) == 405, f"expected 405 got {status!r}"
    data = json.loads(body)
    assert "error" in data, f"expected 'error' key in {data!r}"


@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code-quality report — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
