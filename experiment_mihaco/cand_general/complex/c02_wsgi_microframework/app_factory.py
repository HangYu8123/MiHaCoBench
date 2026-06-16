"""app_factory.py — create_app() entry point for the demo application."""

import sys
import os

# Ensure the directory containing this file is on the path so relative imports work
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

import jinja2

from app import App
from http import Request, Response


def create_app():
    """Build and return a WSGI-compatible callable (the demo application)."""
    app = App()

    @app.route("/", methods=["GET"])
    def index(request: Request) -> Response:
        template = jinja2.Template("<html>PyBench</html>")
        html_body = template.render()
        response = Response()
        response.status_code = 200
        # Keep default Content-Type: text/html; charset=utf-8
        response.body = html_body.encode("utf-8")
        return response

    @app.route("/hello/<name>", methods=["GET"])
    def hello(request: Request) -> Response:
        name = request.path_params["name"]
        response = Response()
        response.set_json({"greeting": f"Hello, {name}!"})
        return response

    @app.route("/add", methods=["GET"])
    def add(request: Request) -> Response:
        response = Response()
        try:
            params = request.query_params()
            a = int(params["a"])
            b = int(params["b"])
            response.set_json({"sum": a + b})
        except (KeyError, ValueError):
            response.status_code = 400
            response.set_json({"error": "invalid parameters"})
        return response

    @app.route("/echo", methods=["POST"])
    def echo(request: Request) -> Response:
        response = Response()
        try:
            body = request.get_json()
            response.set_json({"you_sent": body})
        except ValueError:
            response.status_code = 400
            response.set_json({"error": "invalid JSON body"})
        return response

    return app
