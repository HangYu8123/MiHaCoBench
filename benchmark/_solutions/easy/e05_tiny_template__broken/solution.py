"""Deliberately-broken reference for easy/e05_tiny_template.

Planted defect: HTML escaping is disabled by default — raw values are
inserted without escaping '&', '<', '>', '"'. The |safe filter also
has no effect (everything is already unescaped).

This causes the grader's HTML-escaping tests to fail.
"""
from __future__ import annotations

import re

_MISSING = object()

_VAR_TAG = re.compile(r"\{\{\s*([\w.]+)\s*(?:\|\s*(safe))?\s*\}\}")
_IF_TAG = re.compile(
    r"\{%\s*if\s+(not\s+)?(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}",
    re.DOTALL,
)
_FOR_TAG = re.compile(
    r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
    re.DOTALL,
)


def _dotted_lookup(context: dict, path: str):
    parts = path.split(".")
    value = context
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _render_vars(fragment: str, context: dict) -> str:
    def _replace(match: re.Match) -> str:
        path = match.group(1)
        value = _dotted_lookup(context, path)
        if value is _MISSING:
            return ""
        # BUG: no HTML escaping at all — |safe filter is also irrelevant
        return str(value)

    return _VAR_TAG.sub(_replace, fragment)


def _render_if(fragment: str, context: dict) -> str:
    def _replace(match: re.Match) -> str:
        negated = bool(match.group(1))
        key = match.group(2)
        body = match.group(3)
        value = context.get(key)
        condition = bool(value)
        if negated:
            condition = not condition
        return body if condition else ""

    return _IF_TAG.sub(_replace, fragment)


def _render_for(fragment: str, context: dict) -> str:
    def _replace(match: re.Match) -> str:
        loop_var = match.group(1)
        items_key = match.group(2)
        body = match.group(3)
        iterable = context.get(items_key)
        if not iterable:
            return ""
        parts: list[str] = []
        for element in iterable:
            child_ctx = dict(context)
            child_ctx[loop_var] = element
            rendered = _render_if(body, child_ctx)
            rendered = _render_vars(rendered, child_ctx)
            parts.append(rendered)
        return "".join(parts)

    return _FOR_TAG.sub(_replace, fragment)


def render(template: str, context: dict) -> str:
    """Render *template* against *context* (broken: no HTML escaping)."""
    result = _render_for(template, context)
    result = _render_if(result, context)
    result = _render_vars(result, context)
    return result
