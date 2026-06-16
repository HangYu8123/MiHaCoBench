"""parser.py — Build a node tree from a list of :class:`~lexer.Token` objects.

Node types
----------
TextNode(text)          — literal text
VarNode(path)           — variable substitution (dotted path)
ForNode(loop_var, items_var, body_nodes)  — loop block
RootNode(children)      — top-level container
"""
from __future__ import annotations

from typing import Any

from lexer import Token, TokenType


# --------------------------------------------------------------------------- #
# AST node types
# --------------------------------------------------------------------------- #

class TextNode:
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text

    def __repr__(self) -> str:  # pragma: no cover
        return f"TextNode({self.text!r})"


class VarNode:
    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path

    def __repr__(self) -> str:  # pragma: no cover
        return f"VarNode({self.path!r})"


class ForNode:
    __slots__ = ("loop_var", "items_var", "body")

    def __init__(self, loop_var: str, items_var: str, body: list[Any]) -> None:
        self.loop_var  = loop_var
        self.items_var = items_var
        self.body      = body

    def __repr__(self) -> str:  # pragma: no cover
        return f"ForNode({self.loop_var!r} in {self.items_var!r}, body={self.body!r})"


class RootNode:
    __slots__ = ("children",)

    def __init__(self, children: list[Any]) -> None:
        self.children = children

    def __repr__(self) -> str:  # pragma: no cover
        return f"RootNode({self.children!r})"


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

def parse(tokens: list[Token]) -> RootNode:
    """Parse a flat token list into a :class:`RootNode` tree.

    Raises :class:`SyntaxError` for mismatched ``{% endfor %}``.
    """
    pos = 0

    def _parse_body() -> list[Any]:
        """Parse tokens until ENDFOR (or end of stream) and return nodes."""
        nonlocal pos
        nodes: list[Any] = []
        while pos < len(tokens):
            tok = tokens[pos]
            if tok.type == TokenType.TEXT:
                nodes.append(TextNode(tok.value))
                pos += 1
            elif tok.type == TokenType.VAR:
                nodes.append(VarNode(tok.value))
                pos += 1
            elif tok.type == TokenType.FOR:
                loop_var, items_var = tok.value.split("|", 1)
                pos += 1
                body = _parse_body()   # recursively parse body
                # Expect ENDFOR at current pos
                if pos < len(tokens) and tokens[pos].type == TokenType.ENDFOR:
                    pos += 1
                # else: malformed template — silently close the loop
                nodes.append(ForNode(loop_var, items_var, body))
            elif tok.type == TokenType.ENDFOR:
                # Caller's _parse_body() should consume it; stop here.
                break
            else:
                pos += 1
        return nodes

    nodes = _parse_body()
    return RootNode(nodes)
