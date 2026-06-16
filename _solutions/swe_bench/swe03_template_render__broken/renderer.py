"""renderer.py — Facade: tokenize → parse → evaluate the node tree.

BROKEN VARIANT: The loop variable scope LEAKS — the child context is mutated
in-place (via the shared reference) instead of creating a fresh copy per
iteration.  As a result, after the inner loop completes, the outer loop's
context has the inner loop variable still bound to the LAST inner element,
causing nested loops to render incorrect values.

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
# Evaluator — BUG: shared context mutated across iterations
# --------------------------------------------------------------------------- #

def _eval_nodes(nodes: list[Any], context: dict) -> str:
    """Recursively render *nodes* against *context*.

    BUG: Instead of creating a fresh copy of the context per loop iteration,
    we write the loop variable directly into the SHARED parent context dict.
    This means:
      - Single flat loops work fine (the outer context doesn't need the var).
      - Nested loops: after the inner loop finishes, the inner loop variable
        remains in the outer context, polluting subsequent outer iterations.
    """
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
                # BUG: write directly into the shared parent context instead
                # of making a fresh child copy.  The inner loop variable
                # bleeds through to the outer context after the inner block.
                context[node.loop_var] = element
                parts.append(_eval_nodes(node.body, context))
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Public facade
# --------------------------------------------------------------------------- #

def render(template: str, context: dict) -> str:
    """Render *template* against *context* and return the resulting string."""
    tokens = tokenize(template)
    tree   = parse(tokens)
    return _eval_nodes(tree.children, context)
