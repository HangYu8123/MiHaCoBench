"""app_factory.py — Factory function to build the demo application."""

import sys
import os

# Ensure this directory is on sys.path so the sibling modules are importable
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

import jinja2

from app import App
from http import Request, Response


def create_app():
    """Build and return a WSGI-compatible callable (the demo application)."""

    application = App()

    # Set up Jinja2 environment with a simple inline template loader
    _INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>PyBench</title></head>
<body><h1>Welcome to PyBench</h1></body>
</html>
"""

    jinja_env = jinja2.Environment(loader=jinja2.BaseLoader())
    index_tmpl = jinja_env.from_string(_INDEX_TEMPLATE)

    # -----------------------------------------------------------------------
    # GET /
    # -----------------------------------------------------------------------
    @application.route("/", methods=["GET"])
    def index(request: Request) -> Response:
        resp = Response()
        resp.status_code = 200
        rendered = index_tmpl.render()
        resp.body = rendered.encode("utf-8")
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp

    # -----------------------------------------------------------------------
    # GET /hello/<name>
    # -----------------------------------------------------------------------
    @application.route("/hello/<name>", methods=["GET"])
    def hello(request: Request) -> Response:
        name = request.path_params.get("name", "")
        resp = Response()
        resp.set_json({"greeting": f"Hello, {name}!"})
        return resp

    # -----------------------------------------------------------------------
    # GET /add  (query params a and b)
    # -----------------------------------------------------------------------
    @application.route("/add", methods=["GET"])
    def add(request: Request) -> Response:
        params = request.query_params()
        resp = Response()
        try:
            a = int(params.get("a", ""))
            b = int(params.get("b", ""))
        except (ValueError, KeyError):
            resp.status_code = 400
            resp.set_json({"error": "parameters 'a' and 'b' must be integers"})
            return resp
        resp.set_json({"sum": a + b})
        return resp

    # -----------------------------------------------------------------------
    # POST /echo
    # -----------------------------------------------------------------------
    @application.route("/echo", methods=["POST"])
    def echo(request: Request) -> Response:
        resp = Response()
        try:
            data = request.get_json()
        except ValueError as exc:
            resp.status_code = 400
            resp.set_json({"error": str(exc)})
            return resp
        resp.set_json({"you_sent": data})
        return resp

    return application
