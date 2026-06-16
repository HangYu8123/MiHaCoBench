"""app_factory.py — Factory function to build the demo WSGI application."""

import importlib.util
import sys
import os

from jinja2 import Template

# Load local modules by path (avoids naming conflicts with stdlib 'http')
_dir = os.path.dirname(os.path.abspath(__file__))


def _load_local(module_name, filename):
    """Load a module from the same directory as this file."""
    key = f'_wsgi_fw_{module_name}'
    if key in sys.modules:
        return sys.modules[key]
    path = os.path.join(_dir, filename)
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


_http = _load_local('http', 'http.py')
Request = _http.Request
Response = _http.Response

_app_mod = _load_local('app', 'app.py')
App = _app_mod.App


def create_app():
    """Build and return a WSGI-compatible callable (the demo application)."""
    app = App()

    @app.route("/", methods=["GET"])
    def index(request: Request) -> Response:
        # Render a template containing "PyBench" via jinja2
        template = Template(
            "<!DOCTYPE html><html><body><h1>PyBench WSGI Micro-Framework</h1></body></html>"
        )
        rendered = template.render()
        resp = Response(status_code=200, body=rendered.encode("utf-8"))
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
        try:
            a = int(params["a"])
            b = int(params["b"])
        except (KeyError, ValueError) as e:
            resp.status_code = 400
            resp.set_json({"error": f"Invalid or missing parameters: {e}"})
            return resp
        resp.set_json({"sum": a + b})
        return resp

    @app.route("/echo", methods=["POST"])
    def echo(request: Request) -> Response:
        resp = Response()
        try:
            data = request.get_json()
        except ValueError as e:
            resp.status_code = 400
            resp.set_json({"error": f"Invalid JSON body: {e}"})
            return resp
        resp.set_json({"you_sent": data})
        return resp

    return app
