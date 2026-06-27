"""app_factory.py — Factory function that builds the demo WSGI application."""

import sys
import os

# Ensure sibling modules are importable
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from http import Response  # noqa: E402  (local http.py)
from app import App  # noqa: E402


def create_app():
    """Build and return a WSGI-compatible callable (the demo application).

    Routes registered:
      GET  /              — HTML page containing "PyBench" (rendered via jinja2)
      GET  /hello/<name>  — JSON {"greeting": "Hello, <name>!"}
      GET  /add           — JSON {"sum": int} or 400 JSON {"error": "..."}
      POST /echo          — JSON {"you_sent": <parsed body>}
    """
    from jinja2 import Environment  # jinja2 is in the allowed packages

    app = App()

    # --- Route: GET / ---
    @app.route("/", methods=["GET"])
    def index(request):
        env = Environment()
        template = env.from_string(
            "<!DOCTYPE html><html><head><title>PyBench</title></head>"
            "<body><h1>PyBench</h1></body></html>"
        )
        response = Response()
        response.status_code = 200
        response.body = template.render().encode("utf-8")
        # Content-Type is already "text/html; charset=utf-8" by default
        return response

    # --- Route: GET /hello/<name> ---
    @app.route("/hello/<name>", methods=["GET"])
    def hello(request):
        name = request.path_params.get("name", "")
        response = Response()
        response.status_code = 200
        response.set_json({"greeting": f"Hello, {name}!"})
        return response

    # --- Route: GET /add ---
    @app.route("/add", methods=["GET"])
    def add(request):
        response = Response()
        params = request.query_params()
        try:
            a = int(params["a"])
            b = int(params["b"])
        except (KeyError, ValueError):
            response.status_code = 400
            response.set_json({"error": "parameters 'a' and 'b' must be integers"})
            return response
        response.status_code = 200
        response.set_json({"sum": a + b})
        return response

    # --- Route: POST /echo ---
    @app.route("/echo", methods=["POST"])
    def echo(request):
        response = Response()
        try:
            data = request.get_json()
        except (ValueError, Exception):
            response.status_code = 400
            response.set_json({"error": "invalid or missing JSON body"})
            return response
        response.status_code = 200
        response.set_json({"you_sent": data})
        return response

    return app
