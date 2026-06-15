"""Gold reference — router.py: Route + Router with path converters."""
from __future__ import annotations

import re
from typing import Callable


# --------------------------------------------------------------------------- #
# Path-pattern compilation
# --------------------------------------------------------------------------- #
# Converter registry: maps converter_name -> (regex_fragment, cast_fn)
_CONVERTERS: dict[str, tuple[str, Callable]] = {
    "str": (r"[^/]+", str),
    "int": (r"[0-9]+", int),
}


def _compile_pattern(path_template: str) -> tuple[re.Pattern, list[tuple[str, Callable]]]:
    """Convert a path template like ``/hello/<name>`` or ``/u/<int:id>`` to a
    compiled regex and an ordered list of ``(param_name, cast_fn)`` pairs."""
    param_info: list[tuple[str, Callable]] = []
    regex_parts: list[str] = []
    last = 0

    for m in re.finditer(r"<(?:(\w+):)?(\w+)>", path_template):
        # Literal text before this param
        regex_parts.append(re.escape(path_template[last : m.start()]))
        converter_name = m.group(1) or "str"
        param_name = m.group(2)
        if converter_name not in _CONVERTERS:
            raise ValueError(f"Unknown converter '{converter_name}'")
        frag, cast_fn = _CONVERTERS[converter_name]
        regex_parts.append(f"(?P<{param_name}>{frag})")
        param_info.append((param_name, cast_fn))
        last = m.end()

    regex_parts.append(re.escape(path_template[last:]))
    pattern = re.compile("^" + "".join(regex_parts) + "$")
    return pattern, param_info


# --------------------------------------------------------------------------- #
# Route
# --------------------------------------------------------------------------- #
class Route:
    """A single URL rule."""

    def __init__(self, path_template: str, methods: list[str], handler: Callable) -> None:
        self.path_template: str = path_template
        self.methods: list[str] = [m.upper() for m in methods]
        self.handler: Callable = handler
        self._pattern, self._param_info = _compile_pattern(path_template)

    def match_path(self, path: str) -> dict | None:
        """Return captured path params (cast to their type) if *path* matches,
        else return None."""
        m = self._pattern.match(path)
        if m is None:
            return None
        params: dict = {}
        for name, cast_fn in self._param_info:
            params[name] = cast_fn(m.group(name))
        return params


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
class Router:
    """Match incoming (path, method) pairs to registered routes."""

    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add_route(self, path_template: str, methods: list[str], handler: Callable) -> None:
        """Register a new Route."""
        self._routes.append(Route(path_template, methods, handler))

    def match(self, path: str, method: str) -> tuple[Callable, dict] | tuple[None, int]:
        """Match *path* and *method*.

        Returns:
            (handler, path_params)  on success.
            (None, 404)             if no route matches the path.
            (None, 405)             if path matches but method does not.
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
