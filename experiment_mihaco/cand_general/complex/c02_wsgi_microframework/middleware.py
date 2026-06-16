"""middleware.py — MiddlewareChain for composing WSGI middleware."""


class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature:
        middleware(environ, start_response, next_app) -> list[bytes]
    """

    def __init__(self, app) -> None:
        self._inner = app
        self._middlewares: list = []

    def use(self, middleware_fn) -> None:
        """Append *middleware_fn* to the chain."""
        self._middlewares.append(middleware_fn)

    def __call__(self, environ: dict, start_response) -> list:
        """Invoke the chain, falling through to the inner app."""
        # Build chain from right to left so that the first added middleware
        # is the outermost (called first).
        next_app = self._inner
        for mw_fn in reversed(self._middlewares):
            # Use an immediately-invoked lambda to capture current values
            next_app = (lambda mw, nxt: lambda e, sr: mw(e, sr, nxt))(mw_fn, next_app)
        return next_app(environ, start_response)
