"""Gold reference — middleware.py: composable WSGI middleware chain."""
from __future__ import annotations

from typing import Callable, List


class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature::

        def mw(environ, start_response, next_app):
            # ... pre-processing ...
            response = next_app(environ, start_response)
            # ... post-processing ...
            return response

    Middleware are applied in insertion order (first ``use``d = outermost).
    """

    def __init__(self, app: Callable) -> None:
        self._app: Callable = app
        self._middlewares: List[Callable] = []

    def use(self, middleware_fn: Callable) -> None:
        """Append *middleware_fn* to the chain (outermost = first appended)."""
        self._middlewares.append(middleware_fn)

    def __call__(self, environ: dict, start_response) -> list[bytes]:
        """Invoke the middleware chain and ultimately the inner app."""
        # Build a chain of partials from innermost (app) out
        def build_chain(index: int) -> Callable:
            if index >= len(self._middlewares):
                return self._app
            mw = self._middlewares[index]
            next_app = build_chain(index + 1)

            def _call(env, sr):
                return mw(env, sr, next_app)

            return _call

        chain = build_chain(0)
        return chain(environ, start_response)
