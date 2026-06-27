"""parser.py — Build a simple node tree from the token list produced by lexer.py."""

from lexer import tokenize, TokenType


# Node types as plain dicts:
#   {"type": "TEXT",  "value": <str>}
#   {"type": "VAR",   "path":  <str>}
#   {"type": "FOR",   "loop_var": <str>, "items_var": <str>, "body": [nodes]}


def _parse_nodes(tokens: list, pos: list) -> list:
    """Recursively parse tokens starting at pos[0].

    Stops when it hits an ENDFOR token (consumed) or the end of the list.
    Returns the list of nodes parsed.
    """
    nodes = []
    while pos[0] < len(tokens):
        tok = tokens[pos[0]]
        pos[0] += 1

        if tok.type == TokenType.TEXT:
            nodes.append({"type": "TEXT", "value": tok.value})

        elif tok.type == TokenType.VAR:
            nodes.append({"type": "VAR", "path": tok.value})

        elif tok.type == TokenType.FOR:
            loop_var, items_var = tok.value.split("|", 1)
            body = _parse_nodes(tokens, pos)  # reads until ENDFOR
            nodes.append({
                "type":      "FOR",
                "loop_var":  loop_var,
                "items_var": items_var,
                "body":      body,
            })

        elif tok.type == TokenType.ENDFOR:
            # End of the current FOR body — return to caller.
            break

    return nodes


def parse(template: str) -> list:
    """Return the root node list for *template*."""
    tokens = tokenize(template)
    pos = [0]
    return _parse_nodes(tokens, pos)
