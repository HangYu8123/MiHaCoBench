"""app.py — Core App class (WSGI entry point)."""

from http import Request, Response
from router import Router
from middleware import MiddlewareChain


class App:
    """Core WSGI application."""

    def __init__(self) -> None:
        self._router = Router()
        self._middleware_chain = MiddlewareChain(self._dispatch)

    def route(self, path: str, methods=None):
        """Decorator factory: register the decorated function as the handler for
        *path* + *methods* (default ["GET"]).
        """
        if methods is None:
            methods = ["GET"]

        def decorator(fn):
            self._router.add_route(path, methods, fn)
            return fn

        return decorator

    def use(self, middleware_fn) -> None:
        """Add a middleware function to the chain."""
        self._middleware_chain.use(middleware_fn)

    def __call__(self, environ: dict, start_response) -> list:
        """WSGI entry point. Dispatch the request; return the response body."""
        return self._middleware_chain(environ, start_response)

    def _dispatch(self, environ: dict, start_response) -> list:
        """Internal dispatcher: match route, invoke handler, return WSGI response."""
        request = Request(environ)
        result = self._router.match(request.path, request.method)

        handler, extra = result

        if handler is None:
            # extra is 404 or 405
            response = Response()
            response.status_code = extra
            if extra == 404:
                response.set_json({"error": "not found"})
            else:
                response.set_json({"error": "method not allowed"})
            return response(environ, start_response)

        # Success path: extra is path_params dict
        request.path_params = extra
        response = handler(request)
        return response(environ, start_response)
