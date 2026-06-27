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
        # Build the chain from the innermost app outward
        # The first middleware added wraps the outermost call
        def make_chain(index):
            if index >= len(self._middlewares):
                # At the end of the middleware list, call the inner app
                return self._app

            def call_next(env, sr):
                next_app = make_chain(index + 1)
                return self._middlewares[index](env, sr, next_app)

            return call_next

        chain = make_chain(0)
        return chain(environ, start_response)
