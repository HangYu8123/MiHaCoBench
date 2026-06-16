"""middleware.py — Middleware chain for the WSGI micro-framework."""


class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature:
        middleware(environ, start_response, next_app) -> list[bytes]
    """

    def __init__(self, app) -> None:
        self._app = app
        self._middlewares: list = []

    def use(self, middleware_fn) -> None:
        """Append *middleware_fn* to the chain."""
        self._middlewares.append(middleware_fn)

    def __call__(self, environ, start_response) -> list:
        """Invoke the chain, falling through to the inner app."""
        # Build the chain from the inner app outward
        # The first middleware in the list is the outermost
        next_app = self._app

        # Build in reverse order so first-added is outermost
        for middleware_fn in reversed(self._middlewares):
            # Capture current next_app and middleware_fn in closure
            def make_next(mw, nxt):
                def call(env, sr):
                    return mw(env, sr, nxt)
                return call

            next_app = make_next(middleware_fn, next_app)

        return next_app(environ, start_response)
