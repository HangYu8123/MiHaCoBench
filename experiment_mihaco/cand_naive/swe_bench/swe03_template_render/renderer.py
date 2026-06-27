"""Renderer — facade module for the minimal template engine.

Public API:
    render(template: str, context: dict) -> str
"""

from parser import parse, TextNode, VarNode, ForNode


# ─── Context helpers ──────────────────────────────────────────────────────────

def _lookup(path: str, context: dict) -> str:
    """Resolve a dotted path in *context*.  Missing keys → empty string."""
    parts = path.split(".")
    value = context
    try:
        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            else:
                return ""
    except (KeyError, TypeError):
        return ""
    return str(value)


# ─── Render helpers ───────────────────────────────────────────────────────────

def _render_nodes(nodes: list, context: dict) -> str:
    parts = []
    for node in nodes:
        if isinstance(node, TextNode):
            parts.append(node.text)

        elif isinstance(node, VarNode):
            parts.append(_lookup(node.path, context))

        elif isinstance(node, ForNode):
            # Resolve the items list
            items = _lookup_raw(node.items_var, context)
            if items is None:
                continue  # missing → empty

            # Save any pre-existing value for the loop variable
            had_prior = node.loop_var in context
            prior_value = context.get(node.loop_var)

            try:
                iterable = iter(items)
            except TypeError:
                continue  # not iterable → empty

            for element in iterable:
                context[node.loop_var] = element
                parts.append(_render_nodes(node.body, context))

            # Restore context (block scoping)
            if had_prior:
                context[node.loop_var] = prior_value
            else:
                context.pop(node.loop_var, None)

    return "".join(parts)


def _lookup_raw(path: str, context: dict):
    """Resolve a dotted path in *context*; return the Python object or None."""
    parts = path.split(".")
    value = context
    try:
        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            else:
                return None
    except (KeyError, TypeError):
        return None
    return value


# ─── Public API ───────────────────────────────────────────────────────────────

def render(template: str, context: dict) -> str:
    """Render *template* string with the given *context* dict."""
    # Work on a shallow copy so the caller's dict is not mutated
    ctx = dict(context)
    nodes = parse(template)
    return _render_nodes(nodes, ctx)
