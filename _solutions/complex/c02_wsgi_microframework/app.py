"""Gold reference — app.py: the core WSGI App class."""
from __future__ import annotations

import traceback
from typing import Callable, List

from http_mod import Request, Response
from router import Router


class App:
    """Core WSGI application with routing."""

    def __init__(self) -> None:
        self._router: Router = Router()

    # ------------------------------------------------------------------
    # Decorator
    # ------------------------------------------------------------------
    def route(self, path: str, methods: list[str] | None = None):
        """Decorator factory: register the decorated function as a route handler.

        Usage::

            @app.route("/hello/<name>", methods=["GET"])
            def hello(request):
                ...
        """
        if methods is None:
            methods = ["GET"]

        def decorator(fn: Callable) -> Callable:
            self._router.add_route(path, methods, fn)
            return fn

        return decorator

    # ------------------------------------------------------------------
    # WSGI entry point
    # ------------------------------------------------------------------
    def __call__(self, environ: dict, start_response) -> list[bytes]:
        """Dispatch the request through the router and return the response."""
        request = Request(environ)
        result = self._router.match(request.path, request.method)

        if result[0] is None:
            error_code = result[1]  # 404 or 405
            if error_code == 404:
                resp = Response(404)
                resp.set_json({"error": "not found"})
            else:
                resp = Response(405)
                resp.set_json({"error": "method not allowed"})
            return resp(environ, start_response)

        handler, path_params = result
        request.path_params = path_params

        try:
            resp = handler(request)
            if not isinstance(resp, Response):
                # Allow handlers to return a bare Response object or nothing
                r = Response(200)
                r.body = str(resp).encode("utf-8")
                resp = r
        except Exception:
            traceback.print_exc()
            resp = Response(500)
            resp.set_json({"error": "internal server error"})

        return resp(environ, start_response)
