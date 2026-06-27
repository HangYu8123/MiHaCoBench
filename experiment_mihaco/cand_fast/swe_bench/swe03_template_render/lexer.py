"""lexer.py — Tokenize a template string into a flat list of tokens."""

import re


class TokenType:
    TEXT   = "TEXT"
    VAR    = "VAR"
    FOR    = "FOR"
    ENDFOR = "ENDFOR"


class Token:
    def __init__(self, type_: str, value: str) -> None:
        self.type  = type_   # one of TokenType.*
        self.value = value   # raw content


# Split on {{ ... }} and {% ... %} — keep the delimiters via a capturing group.
_TAG_RE = re.compile(r'(\{\{.*?\}\}|\{%.*?%\})', re.DOTALL)


def tokenize(template: str) -> list:
    """Return an ordered list of Token objects for *template*."""
    tokens: list = []
    for part in _TAG_RE.split(template):
        if not part:
            continue
        if part.startswith("{{") and part.endswith("}}"):
            inner = part[2:-2].strip()
            tokens.append(Token(TokenType.VAR, inner))
        elif part.startswith("{%") and part.endswith("%}"):
            inner = part[2:-2].strip()
            words = inner.split()
            if words[0] == "for":
                # {% for loop_var in items_var %}
                loop_var  = words[1]
                items_var = words[3]
                tokens.append(Token(TokenType.FOR, f"{loop_var}|{items_var}"))
            elif words[0] == "endfor":
                tokens.append(Token(TokenType.ENDFOR, ""))
        else:
            # Plain literal text
            tokens.append(Token(TokenType.TEXT, part))
    return tokens
