from path import split_path


class Router:
    def __init__(self) -> None:
        self._routes: list[tuple[list[str], str]] = []

    def add(self, pattern: str, handler_name: str) -> None:
        """Register handler_name for pattern (e.g. "/users/{id}/posts/{pid}")."""
        self._routes.append((split_path(pattern), handler_name))

    def match(self, path: str) -> tuple[str, dict] | None:
        """Return (handler_name, params) for the first matching route, else None."""
        path_segs = split_path(path)
        for pat_segs, handler in self._routes:
            if len(pat_segs) != len(path_segs):
                continue
            params = {}
            for ps, seg in zip(pat_segs, path_segs):
                if ps.startswith("{") and ps.endswith("}"):
                    params[ps[1:-1]] = seg
                elif ps != seg:
                    break
            else:
                return handler, params
        return None
