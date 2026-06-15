"""Gold reference for easy/e05_tiny_template — tiny Jinja-like template renderer."""
from __future__ import annotations

import re


# --------------------------------------------------------------------------- #
# HTML escaping
# --------------------------------------------------------------------------- #

_HTML_ESCAPES: list[tuple[str, str]] = [
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
]


def _html_escape(text: str) -> str:
    """Escape the four HTML-special characters in *text*."""
    for char, entity in _HTML_ESCAPES:
        text = text.replace(char, entity)
    return text


# --------------------------------------------------------------------------- #
# Context lookup helpers
# --------------------------------------------------------------------------- #

def _dotted_lookup(context: dict, path: str):
    """Resolve a dotted key path like 'a.b.c' in *context*.

    Returns the value on success, or *None* if any step is missing.
    Missing is signalled by returning the sentinel _MISSING.
    """
    parts = path.split(".")
    value = context
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


_MISSING = object()  # sentinel for missing keys


def _resolve(context: dict, path: str):
    """Look up *path* (possibly dotted) in *context*. Returns (_MISSING, False)
    on failure, or (value, True) on success."""
    v = _dotted_lookup(context, path)
    if v is _MISSING:
        return _MISSING, False
    return v, True


# --------------------------------------------------------------------------- #
# Tag regexes
# --------------------------------------------------------------------------- #

# {{ varname }} or {{ varname|safe }}  — var tags
_VAR_TAG = re.compile(r"\{\{\s*([\w.]+)\s*(?:\|\s*(safe))?\s*\}\}")

# {% if [not] name %}...{% endif %}
_IF_TAG = re.compile(
    r"\{%\s*if\s+(not\s+)?(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}",
    re.DOTALL,
)

# {% for x in items %}...{% endfor %}
_FOR_TAG = re.compile(
    r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
    re.DOTALL,
)


# --------------------------------------------------------------------------- #
# Core renderer
# --------------------------------------------------------------------------- #

def _render_vars(fragment: str, context: dict) -> str:
    """Replace all {{ ... }} variable tags in *fragment* using *context*."""
    def _replace(match: re.Match) -> str:
        path = match.group(1)
        is_safe = match.group(2) == "safe"
        value, found = _resolve(context, path)
        if not found:
            return ""
        text = str(value)
        return text if is_safe else _html_escape(text)

    return _VAR_TAG.sub(_replace, fragment)


def _render_for(fragment: str, context: dict) -> str:
    """Expand all {% for x in items %}...{% endfor %} blocks in *fragment*."""
    def _replace(match: re.Match) -> str:
        loop_var = match.group(1)
        items_key = match.group(2)
        body = match.group(3)
        iterable = context.get(items_key)
        if not iterable:
            return ""
        parts: list[str] = []
        for element in iterable:
            # Build a child context: inherit parent, override the loop variable.
            child_ctx = dict(context)
            child_ctx[loop_var] = element
            # Render any nested if-blocks, then var tags.
            rendered = _render_if(body, child_ctx)
            rendered = _render_vars(rendered, child_ctx)
            parts.append(rendered)
        return "".join(parts)

    return _FOR_TAG.sub(_replace, fragment)


def _render_if(fragment: str, context: dict) -> str:
    """Expand all {% if [not] name %}...{% endif %} blocks in *fragment*."""
    def _replace(match: re.Match) -> str:
        negated = bool(match.group(1))  # "not " present?
        key = match.group(2)
        body = match.group(3)
        value = context.get(key)
        condition = bool(value)
        if negated:
            condition = not condition
        return body if condition else ""

    return _IF_TAG.sub(_replace, fragment)


def render(template: str, context: dict) -> str:
    """Render *template* against *context*.

    Processing order: for-loops first (they may contain if/var tags in their
    bodies), then if-blocks, then variable tags.
    """
    result = _render_for(template, context)
    result = _render_if(result, context)
    result = _render_vars(result, context)
    return result
