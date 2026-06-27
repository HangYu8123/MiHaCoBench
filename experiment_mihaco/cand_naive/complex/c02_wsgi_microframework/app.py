"""app.py — Core WSGI App class."""

from http import Request, Response
from router import Router
from middleware import MiddlewareChain


class App:
    """Core WSGI application."""

    def __init__(self) -> None:
        self._router = Router()
        self._middleware = MiddlewareChain(self._dispatch)

    def route(self, path: str, methods=None):
        """Decorator factory: register the decorated function as the handler for
        *path* + *methods* (default ["GET"]).
        """
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            self._router.add_route(path, methods, handler)
            return handler

        return decorator

    def use(self, middleware_fn) -> None:
        """Add a middleware to the chain."""
        self._middleware.use(middleware_fn)

    def _dispatch(self, environ: dict, start_response) -> list:
        """Internal WSGI dispatch — called by the middleware chain."""
        request = Request(environ)
        response = Response()

        result = self._router.match(request.path, request.method)
        handler, extra = result

        if handler is None:
            # extra is 404 or 405
            status_code = extra
            if status_code == 404:
                response.status_code = 404
                response.set_json({"error": "not found"})
            else:
                response.status_code = 405
                response.set_json({"error": "method not allowed"})
        else:
            path_params = extra
            request.path_params = path_params
            # Call the handler with the request; handler returns a Response
            result = handler(request)
            if isinstance(result, Response):
                response = result
            else:
                # If the handler returns something else, treat as body
                response.body = str(result).encode("utf-8")

        return response(environ, start_response)

    def __call__(self, environ: dict, start_response) -> list:
        """WSGI entry point. Dispatch the request; return the response body."""
        return self._middleware(environ, start_response)
