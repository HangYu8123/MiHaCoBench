"""middleware.py — MiddlewareChain for stacking WSGI middleware."""


class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature:
        middleware(environ, start_response, next_app) -> list[bytes]

    Middleware is applied in the order it was added via use(), i.e. the first
    middleware added is the outermost wrapper.
    """

    def __init__(self, app) -> None:
        self._app = app
        self._middleware: list = []

    def use(self, middleware_fn) -> None:
        """Append middleware_fn to the chain."""
        self._middleware.append(middleware_fn)

    def __call__(self, environ, start_response) -> list:
        """Invoke the chain, falling through to the inner app."""
        # Build the chain: wrap innermost (self._app) first,
        # then fold middleware list in reverse so each wraps the previous.
        # The innermost next_app is the raw WSGI app (takes environ, start_response).
        # Middleware is (environ, start_response, next_app) -> list[bytes].

        def make_chain(middlewares, inner_app):
            """Recursively build callable chain from middleware list."""
            if not middlewares:
                return inner_app
            # The current middleware is middlewares[0], rest goes deeper
            current = middlewares[0]
            rest_app = make_chain(middlewares[1:], inner_app)

            def chained(env, sr):
                return current(env, sr, rest_app)

            return chained

        chain = make_chain(self._middleware, self._app)
        return chain(environ, start_response)
