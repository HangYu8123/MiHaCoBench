"""router.py — Route and Router classes for the WSGI micro-framework."""

import re


class Route:
    """Represents a single URL rule."""

    def __init__(self, path_template: str, methods: list, handler) -> None:
        self.path_template = path_template
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        # Pre-compile the regex pattern and store converter info
        self._pattern, self._converters = _compile_template(path_template)

    def match_path(self, path: str):
        """Try to match path. Returns dict of path_params or None if no match."""
        m = self._pattern.fullmatch(path)
        if m is None:
            return None
        raw_params = m.groupdict()
        params = {}
        for name, value in raw_params.items():
            converter = self._converters.get(name, "str")
            if converter == "int":
                params[name] = int(value)
            else:
                params[name] = value
        return params


def _compile_template(path_template: str):
    """Compile a path template into a regex pattern and a dict of converters.

    Supported converters:
      <name>       -> matches any non-empty non-slash segment, captured as str
      <int:name>   -> matches decimal integer segment, captured as int
    """
    converters = {}
    # Replace <int:name> and <name> with named regex groups
    pattern = ""
    i = 0
    while i < len(path_template):
        if path_template[i] == "<":
            end = path_template.index(">", i)
            spec = path_template[i + 1:end]
            if ":" in spec:
                converter, name = spec.split(":", 1)
                converter = converter.strip()
            else:
                converter = "str"
                name = spec.strip()
            converters[name] = converter
            if converter == "int":
                pattern += f"(?P<{name}>[0-9]+)"
            else:
                pattern += f"(?P<{name}>[^/]+)"
            i = end + 1
        else:
            pattern += re.escape(path_template[i])
            i += 1
    return re.compile(pattern), converters


class Router:
    """Match incoming paths to registered routes."""

    def __init__(self) -> None:
        self._routes: list = []

    def add_route(self, path_template: str, methods: list, handler) -> None:
        """Register a new Route."""
        route = Route(path_template, methods, handler)
        self._routes.append(route)

    def match(self, path: str, method: str):
        """Match *path* and *method*.

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
                    return route.handler, params

        if path_matched:
            return None, 405
        return None, 404
