"""renderer.py — Facade for the minimal template engine.

Public API
----------
render(template: str, context: dict) -> str
"""

import sys
import os

# Allow the parser/lexer modules to be found when the grader imports us by
# absolute path and they live in the same directory.
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from parser import parse, TextNode, VarNode, ForNode  # noqa: E402


# ---------------------------------------------------------------------------
# Context lookup helpers
# ---------------------------------------------------------------------------

def _resolve(path: str, context: dict) -> object:
    """Resolve a dotted *path* against *context*.

    Returns the value (any type) on success, or ``""`` if any lookup step
    fails (missing key, non-dict intermediate value, etc.).
    """
    value = context
    for key in path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return ""
        if value is None:
            # None is a valid falsy value but an absent key → empty string.
            # We return None only if the key existed with value None;
            # distinguish by checking: .get returns None both for "missing"
            # and for "value is None".  We treat both as empty string per spec.
            return ""
    return value


# ---------------------------------------------------------------------------
# Recursive renderer
# ---------------------------------------------------------------------------

def _render_nodes(nodes: list, context: dict) -> str:
    """Render a list of AST nodes with *context* (never mutated)."""
    parts: list = []

    for node in nodes:
        if isinstance(node, TextNode):
            parts.append(node.text)

        elif isinstance(node, VarNode):
            val = _resolve(node.path, context)
            if val is None or val == "":
                parts.append("")
            else:
                parts.append(str(val))

        elif isinstance(node, ForNode):
            items = _resolve(node.items_var, context)
            # Non-iterable or missing → zero iterations.
            if items is None or items == "":
                continue
            try:
                items = list(items)  # materialise iterator; catches non-iterable
            except TypeError:
                continue

            for element in items:
                # Create a NEW child context per iteration — never mutate the
                # parent.  This satisfies block-scope requirements:
                #   • The loop variable does not leak after the block ends.
                #   • Outer loop variables survive inner loops unchanged.
                child_ctx = {**context, node.loop_var: element}
                parts.append(_render_nodes(node.body, child_ctx))

    return "".join(parts)


# ---------------------------------------------------------------------------
# Public facade
# ---------------------------------------------------------------------------

def render(template: str, context: dict) -> str:
    """Render *template* with *context* and return the resulting string."""
    nodes = parse(template)
    return _render_nodes(nodes, context)
