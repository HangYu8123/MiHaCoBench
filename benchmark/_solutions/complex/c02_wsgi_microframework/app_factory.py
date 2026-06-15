"""Gold reference — app_factory.py: create_app() returns the demo WSGI application."""
from __future__ import annotations

import os
import sys

# Ensure the solution directory is on sys.path so sibling imports work
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from app import App
from http_mod import Request, Response

import jinja2


# ---------------------------------------------------------------------------
# Jinja2 environment (inline template — no file system needed)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def create_app() -> App:
    """Build and return the demo WSGI application."""
    app = App()

    # ------------------------------------------------------------------ GET /
    @app.route("/", methods=["GET"])
    def index(request: Request) -> Response:
        html = _index_tmpl.render()
        resp = Response(200, html.encode("utf-8"))
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp

    # ---------------------------------------------------- GET /hello/<name>
    @app.route("/hello/<name>", methods=["GET"])
    def hello(request: Request) -> Response:
        name = request.path_params.get("name", "")
        resp = Response()
        resp.set_json({"greeting": f"Hello, {name}!"})
        return resp

    # ------------------------------------------------------ GET /add?a=&b=
    @app.route("/add", methods=["GET"])
    def add(request: Request) -> Response:
        params = request.query_params()
        resp = Response()
        try:
            a = int(params["a"])
            b = int(params["b"])
        except (KeyError, ValueError, TypeError):
            resp.status_code = 400
            resp.set_json({"error": "query params 'a' and 'b' must be integers"})
            return resp
        resp.set_json({"sum": a + b})
        return resp

    # ------------------------------------------------------ POST /echo
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
