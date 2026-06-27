"""WSGI micro-framework — middleware.py: middleware chain."""


class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature:
        middleware(environ, start_response, next_app) -> list[bytes]
    """

    def __init__(self, app) -> None:
        self._app = app
        self._stack: list = []

    def use(self, middleware_fn) -> None:
        """Append *middleware_fn* to the chain."""
        self._stack.append(middleware_fn)

    def __call__(self, environ, start_response) -> list:
        """Invoke the chain, falling through to the inner app.

        Build the chain from inside out (right to left) so that the first
        registered middleware is outermost (runs first). Use default-argument
        capture to avoid the late-binding closure trap.
        """
        # Start with the inner app
        app = self._app

        # Wrap from right to left — each iteration captures the current `app`
        for mw in reversed(self._stack):
            # Default-argument capture freezes `_mw` and `_next` at this iteration
            def make_next(next_app, mw_fn):
                def _call(env, sr):
                    return mw_fn(env, sr, next_app)
                return _call

            app = make_next(app, mw)

        return app(environ, start_response)
