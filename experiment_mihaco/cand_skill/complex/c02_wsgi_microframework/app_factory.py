"""WSGI micro-framework — app_factory.py: demo application factory."""

from jinja2 import Template

from app import App
from http import Response


def create_app():
    """Build and return a WSGI-compatible callable (the demo application)."""
    app = App()

    @app.route("/", methods=["GET"])
    def index(request):
        html = Template(
            "<!DOCTYPE html><html><body><h1>PyBench</h1></body></html>"
        ).render()
        response = Response()
        response.status_code = 200
        response.body = html.encode("utf-8")
        # Content-Type stays as text/html; charset=utf-8 (default)
        return response

    @app.route("/hello/<name>", methods=["GET"])
    def hello(request):
        name = request.path_params["name"]
        response = Response()
        response.status_code = 200
        response.set_json({"greeting": f"Hello, {name}!"})
        return response

    @app.route("/add", methods=["GET"])
    def add(request):
        params = request.query_params()
        response = Response()
        try:
            a = int(params["a"])
            b = int(params["b"])
            response.status_code = 200
            response.set_json({"sum": a + b})
        except (KeyError, ValueError, TypeError):
            response.status_code = 400
            response.set_json({"error": "invalid or missing parameters a and b"})
        return response

    @app.route("/echo", methods=["POST"])
    def echo(request):
        response = Response()
        try:
            data = request.get_json()
            response.status_code = 200
            response.set_json({"you_sent": data})
        except ValueError as exc:
            response.status_code = 400
            response.set_json({"error": str(exc)})
        return response

    return app
