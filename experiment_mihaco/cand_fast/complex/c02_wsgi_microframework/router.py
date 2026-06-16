"""router.py — Route and Router classes with path converter support."""

import re


class Route:
    """Represents a single URL rule."""

    def __init__(self, path_template: str, methods: list, handler) -> None:
        self.path_template = path_template
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        # Compile the path template into a regex pattern and record converter types
        self._pattern, self._converters = self._compile(path_template)

    def _compile(self, template: str):
        """Convert a path template into a compiled regex and a dict of
        param_name -> converter ('str' or 'int')."""
        converters = {}
        # Escape the template for regex, then replace the converter placeholders
        # We need to handle <int:name> and <name> specially before escaping.
        # Split by the converter tokens to build regex segments.
        parts = re.split(r'(<(?:int:)?[^>]+>)', template)
        regex_parts = []
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                inner = part[1:-1]
                if inner.startswith('int:'):
                    name = inner[4:]
                    converters[name] = 'int'
                    regex_parts.append(f'(?P<{name}>[0-9]+)')
                else:
                    name = inner
                    converters[name] = 'str'
                    regex_parts.append(f'(?P<{name}>[^/]+)')
            else:
                regex_parts.append(re.escape(part))
        pattern = re.compile('^' + ''.join(regex_parts) + '$')
        return pattern, converters

    def match_path(self, path: str):
        """Try to match path against this route's pattern.
        Returns a dict of captured params on success, or None on failure."""
        m = self._pattern.match(path)
        if m is None:
            return None
        params = {}
        for name, value in m.groupdict().items():
            if self._converters.get(name) == 'int':
                params[name] = int(value)
            else:
                params[name] = value
        return params


class Router:
    """Match incoming paths to registered routes."""

    def __init__(self) -> None:
        self._routes: list = []

    def add_route(self, path_template: str, methods: list, handler) -> None:
        """Register a new Route."""
        self._routes.append(Route(path_template, methods, handler))

    def match(self, path: str, method: str) -> tuple:
        """Match path and method.

        Returns (handler, path_params) on success.
        Returns (None, 404) if no route matches the path.
        Returns (None, 405) if the path matches but the method does not.
        """
        method = method.upper()
        path_matched = False
        for route in self._routes:
            params = route.match_path(path)
            if params is not None:
                path_matched = True
                if method in route.methods:
                    return (route.handler, params)
        if path_matched:
            return (None, 405)
        return (None, 404)
