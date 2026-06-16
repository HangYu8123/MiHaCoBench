"""router.py — pattern registration and matching for the tiny router.

Patterns look like ``/users/{id}/posts/{pid}``. A literal segment must match
the path segment exactly; a ``{name}`` segment captures the corresponding path
segment (as a string) into the params dict. Both the pattern and the incoming
path are normalized with :func:`path.split_path`, so matching is driven purely
by the normalized segment lists.
"""
from __future__ import annotations

from typing import Optional

import path as _path


class Router:
    """Ordered collection of (pattern, handler_name) routes."""

    def __init__(self) -> None:
        # Each entry: (segments, handler_name) where segments is the normalized
        # list of pattern segments (literals and "{name}" captures).
        self._routes: list[tuple[list[str], str]] = []

    def add(self, pattern: str, handler_name: str) -> None:
        """Register ``handler_name`` for ``pattern`` (e.g. ``/users/{id}``)."""
        segments = _path.split_path(pattern)
        self._routes.append((segments, handler_name))

    def match(self, path_str: str) -> Optional[tuple[str, dict]]:
        """Return ``(handler_name, params)`` for the first matching route, else None.

        A route matches iff its normalized pattern segments and the normalized
        path segments have EQUAL length, every literal segment is equal, and
        every ``{name}`` segment binds the path segment into ``params``.
        """
        path_segments = _path.split_path(path_str)
        for pattern_segments, handler_name in self._routes:
            if len(pattern_segments) != len(path_segments):
                continue
            params: dict = {}
            ok = True
            for pat_seg, path_seg in zip(pattern_segments, path_segments):
                if pat_seg.startswith("{") and pat_seg.endswith("}"):
                    params[pat_seg[1:-1]] = path_seg
                elif pat_seg != path_seg:
                    ok = False
                    break
            if ok:
                return handler_name, params
        return None
