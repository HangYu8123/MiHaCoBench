"""app.py — Core App class for the WSGI micro-framework."""

import sys
import os

# Ensure sibling modules are importable when this file is run directly
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from http import Request, Response  # noqa: E402 (local http.py)
from router import Router  # noqa: E402
from middleware import MiddlewareChain  # noqa: E402


class App:
    """Core WSGI application."""

    def __init__(self) -> None:
        self.router = Router()
        self.middleware_chain = MiddlewareChain(self._dispatch)

    def route(self, path: str, methods=None):
        """Decorator factory: register the decorated function as the handler for
        *path* + *methods* (default ``["GET"]``)."""
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            self.router.add_route(path, methods, handler)
            return handler

        return decorator

    def __call__(self, environ: dict, start_response) -> list:
        """WSGI entry point. Dispatch the request; return the response body."""
        return self.middleware_chain(environ, start_response)

    def _dispatch(self, environ: dict, start_response) -> list:
        """Internal dispatcher: build Request, match route, call handler."""
        request = Request(environ)
        result, extra = self.router.match(request.path, request.method)

        if result is None:
            # extra is an integer status code (404 or 405)
            status_code = extra
            response = Response()
            response.status_code = status_code
            if status_code == 404:
                response.set_json({"error": "not found"})
            elif status_code == 405:
                response.set_json({"error": "method not allowed"})
            else:
                response.set_json({"error": "error"})
            return response(environ, start_response)

        # result is the handler, extra is path_params dict
        handler = result
        path_params = extra
        request.path_params = path_params

        response = handler(request)
        return response(environ, start_response)
