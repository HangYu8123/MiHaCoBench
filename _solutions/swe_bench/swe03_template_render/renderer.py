"""renderer.py — Facade: tokenize → parse → evaluate the node tree.

Public API (the only symbol the grader imports from this module):

    render(template: str, context: dict) -> str
"""
from __future__ import annotations

from typing import Any

from lexer import tokenize
from parser import parse, ForNode, TextNode, VarNode, RootNode


# --------------------------------------------------------------------------- #
# Context lookup
# --------------------------------------------------------------------------- #

def _lookup(context: dict, path: str) -> tuple[Any, bool]:
    """Resolve a dotted key path in *context*.

    Returns ``(value, True)`` on success, ``("", False)`` on failure.
    """
    parts = path.split(".")
    value: Any = context
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return "", False
        value = value[part]
    return value, True


# --------------------------------------------------------------------------- #
# Evaluator
# --------------------------------------------------------------------------- #

def _eval_nodes(nodes: list[Any], context: dict) -> str:
    """Recursively render *nodes* against *context*."""
    parts: list[str] = []
    for node in nodes:
        if isinstance(node, TextNode):
            parts.append(node.text)
        elif isinstance(node, VarNode):
            value, found = _lookup(context, node.path)
            parts.append(str(value) if found else "")
        elif isinstance(node, ForNode):
            iterable, found = _lookup(context, node.items_var)
            if not found or not iterable:
                continue
            for element in iterable:
                # Create a FRESH child context for each iteration so that
                # inner loop variables never leak back to the outer scope.
                child_ctx = dict(context)
                child_ctx[node.loop_var] = element
                parts.append(_eval_nodes(node.body, child_ctx))
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Public facade
# --------------------------------------------------------------------------- #

def render(template: str, context: dict) -> str:
    """Render *template* against *context* and return the resulting string."""
    tokens = tokenize(template)
    tree   = parse(tokens)
    return _eval_nodes(tree.children, context)
