"""parser.py — Build a simple AST from a token list.

Node types
----------
TextNode  — literal text
VarNode   — variable / dotted path lookup
ForNode   — loop block with a body list of child nodes
"""

from lexer import TokenType, tokenize


# ---------------------------------------------------------------------------
# AST node classes
# ---------------------------------------------------------------------------

class TextNode:
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text

    def __repr__(self) -> str:  # pragma: no cover
        return f"TextNode({self.text!r})"


class VarNode:
    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path  # e.g. "user.name" or "item"

    def __repr__(self) -> str:  # pragma: no cover
        return f"VarNode({self.path!r})"


class ForNode:
    __slots__ = ("loop_var", "items_var", "body")

    def __init__(self, loop_var: str, items_var: str, body: list) -> None:
        self.loop_var  = loop_var
        self.items_var = items_var  # dotted path allowed
        self.body      = body

    def __repr__(self) -> str:  # pragma: no cover
        return f"ForNode({self.loop_var!r} in {self.items_var!r}, body={self.body!r})"


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------

def _parse_tokens(tokens: list, pos: int, stop_on_endfor: bool):
    """Parse tokens starting at *pos*.

    Returns ``(nodes, new_pos)`` where *nodes* is a list of AST nodes and
    *new_pos* points to the token that ended parsing (either past the end of
    the list or the ENDFOR that closed an inner block).
    """
    nodes: list = []

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
            body, pos = _parse_tokens(tokens, pos, stop_on_endfor=True)
            # pos now points at the ENDFOR token — consume it.
            if pos < len(tokens) and tokens[pos].type == TokenType.ENDFOR:
                pos += 1
            nodes.append(ForNode(loop_var, items_var, body))

        elif tok.type == TokenType.ENDFOR:
            if stop_on_endfor:
                # Return without consuming; caller will consume it.
                break
            # Unexpected ENDFOR at top level — skip it.
            pos += 1

        else:
            pos += 1

    return nodes, pos


def parse(template: str) -> list:
    """Return a list of AST nodes for *template*."""
    tokens = tokenize(template)
    nodes, _ = _parse_tokens(tokens, 0, stop_on_endfor=False)
    return nodes
