"""app.py — Core WSGI App class."""

import importlib.util
import sys
import os

# Load http.py from the same directory (avoids conflict with stdlib 'http')
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

_router = _load_local('router', 'router.py')
Router = _router.Router


class App:
    """Core WSGI application."""

    def __init__(self) -> None:
        self.router = Router()

    def route(self, path: str, methods=None):
        """Decorator factory: register the decorated function as the handler for
        path + methods (default ["GET"])."""
        if methods is None:
            methods = ["GET"]

        def decorator(fn):
            self.router.add_route(path, methods, fn)
            return fn

        return decorator

    def __call__(self, environ: dict, start_response) -> list:
        """WSGI entry point. Dispatch the request; return the response body."""
        request = Request(environ)
        result = self.router.match(request.path, request.method)
        handler, extra = result

        if handler is None:
            # extra is 404 or 405
            resp = Response(status_code=extra)
            if extra == 404:
                resp.set_json({"error": "not found"})
            else:
                resp.set_json({"error": "method not allowed"})
            return resp(environ, start_response)

        # handler found, extra is the path_params dict
        request.path_params = extra
        response = handler(request)
        return response(environ, start_response)
