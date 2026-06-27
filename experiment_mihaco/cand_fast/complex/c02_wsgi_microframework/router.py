"""router.py — Route and Router classes for path matching with converters."""

import re


class Route:
    """Represents a single URL rule."""

    def __init__(self, path_template: str, methods: list, handler) -> None:
        self.path_template: str = path_template
        self.methods: list = [m.upper() for m in methods]
        self.handler = handler

        # Track which captured param names are int-typed
        self.int_params: set = set()

        # Build regex from path template.
        # Strategy: replace all <...> tokens in a single pass to avoid
        # the str-converter regex matching inside already-substituted patterns.
        # Token forms: <int:name> or <name>
        pattern = path_template

        def replace_converter(match):
            token = match.group(1)  # e.g. "int:id" or "name"
            if token.startswith("int:"):
                name = token[4:]
                self.int_params.add(name)
                return "(?P<" + name + ">\\d+)"
            else:
                name = token
                return "(?P<" + name + ">[^/]+)"

        # Match only raw template tokens: <word> or <int:word>
        # The pattern r"<([^>]+)>" on the original (un-substituted) template is safe
        # because we do a single-pass replacement.
        pattern = re.sub(r"<([^>]+)>", replace_converter, pattern)

        # Anchor the pattern
        self.regex = re.compile(f"^{pattern}$")


class Router:
    """Match incoming paths to registered routes."""

    def __init__(self) -> None:
        self._routes: list = []

    def add_route(self, path_template: str, methods: list, handler) -> None:
        """Register a new Route."""
        self._routes.append(Route(path_template, methods, handler))

    def match(self, path: str, method: str) -> tuple:
        """Match *path* and *method*.

        Returns ``(handler, path_params)`` on success.
        Returns ``(None, 404)`` if no route matches the path.
        Returns ``(None, 405)`` if the path matches but the method does not.

        Two-pass algorithm: first collect all path-matching routes, then check
        method. This ensures correct 405 vs 404 discrimination.
        """
        method_upper = method.upper()

        # First pass: find all routes whose regex matches the path
        path_matching = []
        for route in self._routes:
            m = route.regex.fullmatch(path)
            if m is not None:
                path_matching.append((route, m))

        if not path_matching:
            return (None, 404)

        # Second pass: find a route that also matches the method
        for route, m in path_matching:
            if method_upper in route.methods:
                # Cast int-typed params
                raw_params = m.groupdict()
                path_params = {
                    k: int(v) if k in route.int_params else v
                    for k, v in raw_params.items()
                }
                return (route.handler, path_params)

        # Path matched but no method matched
        return (None, 405)
