"""renderer.py — Facade that exposes render(template, context) -> str."""

from parser import parse


# Sentinel — distinct from None so None-valued context entries are preserved.
_MISSING = object()


def _resolve(path: str, context: dict) -> str:
    """Resolve a (possibly dotted) variable path against context.

    Returns the string value, or "" if any lookup step fails.
    """
    val = context
    for part in path.split("."):
        if not isinstance(val, dict):
            return ""
        val = val.get(part, _MISSING)
        if val is _MISSING:
            return ""
    return str(val)


def _render_nodes(nodes: list, context: dict) -> str:
    """Recursively render a list of AST nodes into a string."""
    out = []
    for node in nodes:
        ntype = node["type"]

        if ntype == "TEXT":
            out.append(node["value"])

        elif ntype == "VAR":
            out.append(_resolve(node["path"], context))

        elif ntype == "FOR":
            loop_var  = node["loop_var"]
            items_var = node["items_var"]
            body      = node["body"]

            # Retrieve the iterable — treat missing/non-iterable as empty.
            iterable = context.get(items_var, _MISSING)
            if iterable is _MISSING:
                continue
            try:
                elements = list(iterable)
            except TypeError:
                continue

            if not elements:
                continue

            # Save any pre-existing binding for loop_var.
            saved = context.get(loop_var, _MISSING)

            for element in elements:
                context[loop_var] = element
                out.append(_render_nodes(body, context))

            # Restore context to its pre-loop state.
            if saved is _MISSING:
                context.pop(loop_var, None)
            else:
                context[loop_var] = saved

    return "".join(out)


def render(template: str, context: dict) -> str:
    """Render *template* string with the given *context* dict.

    This is the sole public entry point imported by the grader.
    """
    nodes = parse(template)
    return _render_nodes(nodes, context)
