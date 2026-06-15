"""Deliberately-broken reference for complex/c02_wsgi_microframework.

Two planted defects so the grader must catch at least one:

  DEFECT 1 — /add does NOT validate that a and b are integers; it accepts
    any string and returns string concatenation instead of integer sum.
    e.g. GET /add?a=foo&b=3 returns 200 {"sum": "foo3"} instead of 400.
    And GET /add?a=3&b=4 returns {"sum": "34"} (string concat) instead of
    {"sum": 7}, failing test_get_add_valid.

  DEFECT 2 — unknown paths return 200 {"error": "not found"} instead of 404,
    failing test_unknown_path_returns_404.

This MUST fail the grader (proves the grader discriminates).
"""
from __future__ import annotations

import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from app import App
from http_mod import Request, Response

import jinja2


_INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><title>PyBench WSGI Demo</title></head>
<body>
  <h1>Welcome to PyBench</h1>
  <p>This page was rendered by the PyBench WSGI micro-framework.</p>
</body>
</html>
"""

_jinja_env = jinja2.Environment(loader=jinja2.BaseLoader())
_index_tmpl = _jinja_env.from_string(_INDEX_TEMPLATE)


class _BrokenApp(App):
    """Overrides __call__ to return 200 for unknown paths (DEFECT 2)."""

    def __call__(self, environ: dict, start_response) -> list[bytes]:
        request = Request(environ)
        result = self._router.match(request.path, request.method)

        if result[0] is None:
            error_code = result[1]
            if error_code == 405:
                resp = Response(405)
                resp.set_json({"error": "method not allowed"})
            else:
                # BUG (DEFECT 2): returns 200 instead of 404
                resp = Response(200)
                resp.set_json({"error": "not found"})
            return resp(environ, start_response)

        handler, path_params = result
        request.path_params = path_params
        try:
            resp = handler(request)
            if not isinstance(resp, Response):
                r = Response(200)
                r.body = str(resp).encode("utf-8")
                resp = r
        except Exception:
            resp = Response(500)
            resp.set_json({"error": "internal server error"})

        return resp(environ, start_response)


def create_app() -> _BrokenApp:
    """Build and return the (broken) demo WSGI application."""
    app = _BrokenApp()

    @app.route("/", methods=["GET"])
    def index(request: Request) -> Response:
        html = _index_tmpl.render()
        resp = Response(200, html.encode("utf-8"))
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp

    @app.route("/hello/<name>", methods=["GET"])
    def hello(request: Request) -> Response:
        name = request.path_params.get("name", "")
        resp = Response()
        resp.set_json({"greeting": f"Hello, {name}!"})
        return resp

    @app.route("/add", methods=["GET"])
    def add(request: Request) -> Response:
        params = request.query_params()
        resp = Response()
        # BUG (DEFECT 1): no int() conversion — string concatenation
        a = params.get("a", "")
        b = params.get("b", "")
        resp.set_json({"sum": a + b})
        return resp

    @app.route("/echo", methods=["POST"])
    def echo(request: Request) -> Response:
        resp = Response()
        try:
            payload = request.get_json()
        except (ValueError, Exception):
            resp.status_code = 400
            resp.set_json({"error": "invalid JSON body"})
            return resp
        resp.set_json({"you_sent": payload})
        return resp

    return app
