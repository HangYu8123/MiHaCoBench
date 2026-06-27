"""WSGI micro-framework — app.py: App class."""

from http import Request, Response
from router import Router
from middleware import MiddlewareChain


class App:
    """Core WSGI application."""

    def __init__(self) -> None:
        self._router = Router()
        self._chain = MiddlewareChain(self._dispatch)

    def route(self, path: str, methods=None):
        """Decorator factory: register the decorated function as the handler for
        *path* + *methods* (default ["GET"])."""
        if methods is None:
            methods = ["GET"]

        def decorator(fn):
            self._router.add_route(path, methods, fn)
            return fn

        return decorator

    def _dispatch(self, environ: dict, start_response) -> list:
        """Internal dispatcher: match route, build Request, call handler."""
        request = Request(environ)
        result = self._router.match(request.path, request.method)

        if result[0] is None:
            # result is (None, status_code)
            _, code = result
            if code == 404:
                error_msg = "not found"
            elif code == 405:
                error_msg = "method not allowed"
            else:
                error_msg = "error"
            response = Response()
            response.status_code = code
            response.set_json({"error": error_msg})
            return response(environ, start_response)

        handler, path_params = result
        request.path_params = path_params
        response = handler(request)
        return response(environ, start_response)

    def __call__(self, environ: dict, start_response) -> list:
        """WSGI entry point. Dispatch the request; return the response body."""
        return self._chain(environ, start_response)
