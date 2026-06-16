"""app_factory.py — Factory function for the demo application."""

import sys
import os

# Ensure the directory containing this file is on the path for imports
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import jinja2

from app import App
from http import Request, Response


# Jinja2 environment for rendering templates
_JINJA_ENV = jinja2.Environment(
    loader=jinja2.BaseLoader(),
    autoescape=True,
)

_HOME_TEMPLATE = _JINJA_ENV.from_string(
    "<!DOCTYPE html><html><head><title>PyBench</title></head>"
    "<body><h1>PyBench</h1><p>Welcome to the PyBench WSGI micro-framework demo.</p></body></html>"
)


def create_app() -> callable:
    """Build and return a WSGI-compatible callable (the demo application).

    The returned callable implements:
      GET /                    -> 200 HTML containing "PyBench" (rendered via jinja2)
      GET /hello/<name>        -> 200 JSON {"greeting": "Hello, <name>!"}
      GET /add                 -> 200 JSON {"sum": <int>} or 400 JSON {"error": "..."}
      POST /echo               -> 200 JSON {"you_sent": <parsed body>}
      any unknown path         -> 404 JSON {"error": "not found"}
      wrong method known path  -> 405 JSON {"error": "method not allowed"}
    """
    application = App()

    @application.route("/", methods=["GET"])
    def home(request: Request, response: Response):
        html = _HOME_TEMPLATE.render()
        response.status_code = 200
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.body = html.encode("utf-8")
        return response

    @application.route("/hello/<name>", methods=["GET"])
    def hello(request: Request, response: Response):
        name = request.path_params.get("name", "")
        response.status_code = 200
        response.set_json({"greeting": f"Hello, {name}!"})
        return response

    @application.route("/add", methods=["GET"])
    def add(request: Request, response: Response):
        params = request.query_params()
        try:
            a = int(params.get("a", ""))
            b = int(params.get("b", ""))
        except (ValueError, KeyError):
            response.status_code = 400
            response.set_json({"error": "Parameters 'a' and 'b' must be valid integers"})
            return response
        response.status_code = 200
        response.set_json({"sum": a + b})
        return response

    @application.route("/echo", methods=["POST"])
    def echo(request: Request, response: Response):
        try:
            data = request.get_json()
        except ValueError as exc:
            response.status_code = 400
            response.set_json({"error": str(exc)})
            return response
        response.status_code = 200
        response.set_json({"you_sent": data})
        return response

    return application
