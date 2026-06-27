"""router.py — Route and Router with path converters."""

import re


class Route:
    """Represents a single URL rule."""

    def __init__(self, path_template: str, methods: list, handler) -> None:
        self.path_template = path_template
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        # Compile the path template into a regex pattern + converter map
        self._pattern, self._converters = _compile_template(path_template)

    def match_path(self, path: str):
        """Try to match *path*. Returns a dict of path params on success, None otherwise."""
        m = self._pattern.fullmatch(path)
        if m is None:
            return None
        params = {}
        for name, value in m.groupdict().items():
            converter = self._converters.get(name, str)
            try:
                params[name] = converter(value)
            except (ValueError, TypeError):
                return None
        return params


def _compile_template(template: str):
    """Convert a URL template like '/hello/<name>' or '/item/<int:id>'
    into a compiled regex and a dict mapping param names to converter callables.
    """
    converters = {}
    # Escape the template for regex, then replace converter segments
    # We process segment by segment to avoid double-escaping
    # Split on the angle-bracket segments
    parts = re.split(r"(<[^>]+>)", template)
    regex_parts = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            inner = part[1:-1]  # strip < >
            if ":" in inner:
                converter_name, param_name = inner.split(":", 1)
                converter_name = converter_name.strip()
                param_name = param_name.strip()
            else:
                converter_name = "str"
                param_name = inner.strip()

            if converter_name == "int":
                regex_parts.append(f"(?P<{param_name}>[0-9]+)")
                converters[param_name] = int
            else:
                # Default: match any non-empty, non-slash segment
                regex_parts.append(f"(?P<{param_name}>[^/]+)")
                converters[param_name] = str
        else:
            regex_parts.append(re.escape(part))

    pattern = re.compile("".join(regex_parts))
    return pattern, converters


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
            if params is None:
                continue
            # Path matches
            path_matched = True
            if method in route.methods:
                return (route.handler, params)

        if path_matched:
            return (None, 405)
        return (None, 404)
