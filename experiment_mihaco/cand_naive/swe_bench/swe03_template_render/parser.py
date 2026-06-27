"""Parser for the minimal template engine.

Builds a simple node tree from the token list produced by the lexer.
"""

from lexer import TokenType, tokenize


# ─── Node types ───────────────────────────────────────────────────────────────

class TextNode:
    def __init__(self, text: str):
        self.text = text


class VarNode:
    def __init__(self, path: str):
        self.path = path  # e.g. "user.name" or "item"


class ForNode:
    def __init__(self, loop_var: str, items_var: str, body: list):
        self.loop_var = loop_var
        self.items_var = items_var
        self.body = body  # list of child nodes


# ─── Parser ───────────────────────────────────────────────────────────────────

def parse(template: str) -> list:
    """Return the root node list for the given template string."""
    tokens = tokenize(template)
    nodes, _ = _parse_nodes(tokens, 0)
    return nodes


def _parse_nodes(tokens: list, pos: int) -> tuple:
    """Parse nodes starting at *pos*, stopping at ENDFOR or end of list.

    Returns (node_list, new_pos).
    """
    nodes = []
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
            pos += 1  # consume FOR token
            body, pos = _parse_nodes(tokens, pos)
            # _parse_nodes returns after consuming ENDFOR
            nodes.append(ForNode(loop_var, items_var, body))

        elif tok.type == TokenType.ENDFOR:
            pos += 1  # consume ENDFOR
            break  # return to parent parse call

        else:
            pos += 1  # skip unknown

    return nodes, pos
