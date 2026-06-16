"""router.py — Route and Router classes for path matching with converters."""

import re


class Route:
    """Represents a single URL rule."""

    def __init__(self, path_template: str, methods: list, handler) -> None:
        self.path_template: str = path_template
        self.methods: list = [m.upper() for m in methods]
        self.handler = handler
        self.regex, self.converters = self._compile(path_template)

    @staticmethod
    def _compile(template: str):
        """Compile path template to regex and converters dict."""
        converters = {}
        # Replace <int:name> and <name> segments with named capture groups
        pattern = ""
        i = 0
        while i < len(template):
            if template[i] == "<":
                end = template.index(">", i)
                segment = template[i + 1:end]
                if ":" in segment:
                    converter, name = segment.split(":", 1)
                    if converter == "int":
                        pattern += f"(?P<{name}>[0-9]+)"
                        converters[name] = int
                    else:
                        # Unknown converter — treat as str
                        pattern += f"(?P<{name}>[^/]+)"
                        converters[name] = str
                else:
                    name = segment
                    pattern += f"(?P<{name}>[^/]+)"
                    # No entry in converters means str (no conversion needed)
                i = end + 1
            else:
                pattern += re.escape(template[i])
                i += 1
        regex = re.compile("^" + pattern + "$")
        return regex, converters


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
        method_upper = method.upper()
        path_matched = False

        for route in self._routes:
            m = route.regex.match(path)
            if m is None:
                continue
            # Path matches this route
            path_matched = True
            if method_upper in route.methods:
                # Method also matches — apply converters
                params = m.groupdict()
                converted = {}
                for k, v in params.items():
                    if k in route.converters:
                        converted[k] = route.converters[k](v)
                    else:
                        converted[k] = v
                return route.handler, converted

        if path_matched:
            return None, 405
        return None, 404
