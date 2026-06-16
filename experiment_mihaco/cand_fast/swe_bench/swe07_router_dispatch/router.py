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
        for pattern_segs, handler_name in self._routes:
            if len(pattern_segs) != len(path_segs):
                continue
            params: dict[str, str] = {}
            matched = True
            for pat_seg, path_seg in zip(pattern_segs, path_segs):
                if pat_seg.startswith('{') and pat_seg.endswith('}'):
                    params[pat_seg[1:-1]] = path_seg
                elif pat_seg != path_seg:
                    matched = False
                    break
            if matched:
                return (handler_name, params)
        return None
