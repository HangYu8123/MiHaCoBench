"""WSGI micro-framework — router.py: Route + Router with path converters."""

import re


class Route:
    """Represents a single URL rule."""

    def __init__(self, path_template: str, methods: list, handler) -> None:
        self.path_template: str = path_template
        self.methods: list = [m.upper() for m in methods]
        self.handler = handler


# Cache compiled regexes to avoid recompilation on every request
_TEMPLATE_CACHE: dict = {}


def _compile_template(path_template: str) -> re.Pattern:
    """Convert a path template to a compiled regex with named groups.

    Converter tokens are replaced BEFORE re.escape so angle brackets (which
    Python 3.7+ re.escape does NOT escape) do not cause issues. We split on
    converter tokens, escape the literal segments, then join with named groups.
    """
    if path_template in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[path_template]

    # Split on converter tokens: <int:name> or <name>
    # Each token is replaced with the appropriate named-group pattern.
    # We build the pattern by alternating literal segments and group patterns.
    converter_re = re.compile(r"<(?:([a-zA-Z_][a-zA-Z0-9_]*):)?([a-zA-Z_][a-zA-Z0-9_]*)>")

    parts = []
    last_end = 0
    for m in converter_re.finditer(path_template):
        # Escape and append the literal segment before this token
        literal = path_template[last_end:m.start()]
        parts.append(re.escape(literal))
        # m.group(1) is the converter type (e.g. "int") or None
        # m.group(2) is the parameter name
        converter = m.group(1)
        name = m.group(2)
        if converter == "int":
            parts.append(f"(?P<{name}>[0-9]+)")
        else:
            parts.append(f"(?P<{name}>[^/]+)")
        last_end = m.end()

    # Append any trailing literal segment
    if last_end < len(path_template):
        parts.append(re.escape(path_template[last_end:]))

    pattern = "".join(parts)
    compiled = re.compile(f"^{pattern}$")
    _TEMPLATE_CACHE[path_template] = compiled
    return compiled


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
            regex = _compile_template(route.path_template)
            m = regex.fullmatch(path)
            if m is None:
                continue

            # Path matches — check method
            path_matched = True
            if method not in route.methods:
                continue

            # Both path and method match — extract and cast params
            raw_params = m.groupdict()
            path_params = {}

            # Detect int-typed captures by re-inspecting the template
            for param_name, raw_value in raw_params.items():
                # Check whether this param was declared as <int:name>
                int_pattern = re.compile(
                    r"<int:" + re.escape(param_name) + r">"
                )
                if int_pattern.search(route.path_template):
                    path_params[param_name] = int(raw_value)
                else:
                    path_params[param_name] = raw_value

            return (route.handler, path_params)

        if path_matched:
            return (None, 405)
        return (None, 404)
