from path import split_path


class Router:
    def __init__(self) -> None:
        self._routes: list[tuple[list[str], str]] = []

    def add(self, pattern: str, handler_name: str) -> None:
        """Register handler_name for pattern (e.g. "/users/{id}/posts/{pid}")."""
        segments = split_path(pattern)
        self._routes.append((segments, handler_name))

    def match(self, path: str) -> tuple[str, dict] | None:
        """Return (handler_name, params) for the first matching route, else None."""
        path_segments = split_path(path)
        for pattern_segments, handler_name in self._routes:
            if len(pattern_segments) != len(path_segments):
                continue
            params = {}
            matched = True
            for pat_seg, path_seg in zip(pattern_segments, path_segments):
                if pat_seg.startswith("{") and pat_seg.endswith("}"):
                    # Capture segment
                    param_name = pat_seg[1:-1]
                    params[param_name] = path_seg
                elif pat_seg != path_seg:
                    matched = False
                    break
            if matched:
                return (handler_name, params)
        return None
