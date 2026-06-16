"""app.py — Core App class for the WSGI micro-framework."""

from http import Request, Response
from router import Router
from middleware import MiddlewareChain


class App:
    """Core WSGI application."""

    def __init__(self) -> None:
        self._router = Router()
        self._middleware_chain: MiddlewareChain | None = None

    def route(self, path: str, methods=None):
        """Decorator factory: register the decorated function as the handler for
        *path* + *methods* (default ["GET"])."""
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            self._router.add_route(path, methods, handler)
            return handler

        return decorator

    def use(self, middleware_fn) -> None:
        """Add a middleware function to the application."""
        if self._middleware_chain is None:
            self._middleware_chain = MiddlewareChain(self._dispatch)
        self._middleware_chain.use(middleware_fn)

    def _dispatch(self, environ: dict, start_response) -> list:
        """Internal dispatch logic."""
        request = Request(environ)
        response = Response()

        handler, result = self._router.match(request.path, request.method)

        if handler is None:
            # result is an error code (404 or 405)
            error_code = result
            response.status_code = error_code
            if error_code == 404:
                response.set_json({"error": "not found"})
            else:
                response.set_json({"error": "method not allowed"})
            return response(environ, start_response)

        # Set path_params on request
        request.path_params = result

        # Call the handler with request and response
        ret = handler(request, response)

        # If handler returned a Response, use it; otherwise use the passed response
        if isinstance(ret, Response):
            response = ret

        return response(environ, start_response)

    def __call__(self, environ: dict, start_response) -> list:
        """WSGI entry point. Dispatch the request; return the response body."""
        if self._middleware_chain is not None:
            return self._middleware_chain(environ, start_response)
        return self._dispatch(environ, start_response)
