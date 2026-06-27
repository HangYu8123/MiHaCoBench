from path import split_path


class Router:
    def __init__(self) -> None:
        self._routes: list[tuple[str, str]] = []

    def add(self, pattern: str, handler_name: str) -> None:
        """Register handler_name for pattern (e.g. "/users/{id}/posts/{pid}")."""
        self._routes.append((pattern, handler_name))

    def match(self, path: str) -> tuple[str, dict] | None:
        """Return (handler_name, params) for the first matching route, else None."""
        path_segments = split_path(path)
        for pattern, handler_name in self._routes:
            pattern_segments = split_path(pattern)
            if len(pattern_segments) != len(path_segments):
                continue
            params = {}
            matched = True
            for pseg, rseg in zip(pattern_segments, path_segments):
                if pseg.startswith("{") and pseg.endswith("}"):
                    name = pseg[1:-1]
                    params[name] = rseg
                elif pseg != rseg:
                    matched = False
                    break
            if matched:
                return (handler_name, params)
        return None
