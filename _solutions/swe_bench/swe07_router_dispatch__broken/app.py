"""app.py — FACADE for the tiny path router.

Public entrypoint: ``from app import App``. ``App`` wires a :class:`router.Router`
and exposes ``route`` (register) and ``handle`` (dispatch). The handle result is
always a dict so callers do not have to special-case the no-match path.
"""
from __future__ import annotations

from router import Router


class App:
    """Tiny path-routing application facade."""

    def __init__(self) -> None:
        self._router = Router()

    def route(self, pattern: str, handler_name: str) -> None:
        """Register ``handler_name`` for ``pattern`` (delegates to Router.add)."""
        self._router.add(pattern, handler_name)

    def handle(self, path: str) -> dict:
        """Dispatch ``path``.

        Returns ``{"handler": <name>, "params": {...}}`` on a match, or
        ``{"handler": None, "params": {}}`` when no registered route matches.
        """
        matched = self._router.match(path)
        if matched is None:
            return {"handler": None, "params": {}}
        handler_name, params = matched
        return {"handler": handler_name, "params": params}


__all__ = ["App"]
