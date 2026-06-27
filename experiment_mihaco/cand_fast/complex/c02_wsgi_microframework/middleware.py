"""middleware.py — Middleware chain for the WSGI micro-framework."""

import functools


class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature:
        middleware(environ, start_response, next_app) -> list[bytes]

    Middleware are called outermost-first (the order they were added via use()).
    """

    def __init__(self, app) -> None:
        self.app = app
        self._middleware: list = []

    def use(self, middleware_fn) -> None:
        """Append *middleware_fn* to the chain."""
        self._middleware.append(middleware_fn)

    def __call__(self, environ, start_response) -> list:
        """Invoke the chain, falling through to the inner app."""
        if not self._middleware:
            return self.app(environ, start_response)

        # Build the chain right-to-left so that the first middleware added is
        # the outermost (called first).
        # For middleware list [m0, m1, m2] and inner app:
        #   chain = m0(environ, start_response, lambda: m1(... lambda: m2(... inner_app)))
        # We fold right: start with the inner app and wrap each middleware around it.
        inner = self.app

        def make_next(mw, next_app):
            """Return a WSGI callable that calls mw with next_app."""
            def caller(e, sr):
                return mw(e, sr, next_app)
            return caller

        # Fold right over the middleware list
        chain = functools.reduce(
            lambda next_app, mw: make_next(mw, next_app),
            reversed(self._middleware),
            inner,
        )

        return chain(environ, start_response)
