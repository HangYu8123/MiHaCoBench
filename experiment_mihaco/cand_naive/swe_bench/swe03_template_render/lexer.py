"""Lexer for the minimal template engine."""

import re


class TokenType:
    TEXT = "TEXT"
    VAR = "VAR"
    FOR = "FOR"
    ENDFOR = "ENDFOR"


class Token:
    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r})"


# Regex that splits on {{ ... }} and {% ... %} blocks
_TAG_RE = re.compile(r"(\{\{.*?\}\}|\{%.*?%\})", re.DOTALL)


def tokenize(template: str) -> list:
    """Tokenize a template string into a flat list of Token objects."""
    tokens = []
    parts = _TAG_RE.split(template)

    for part in parts:
        if not part:
            continue

        if part.startswith("{{") and part.endswith("}}"):
            # Variable tag: {{ var_path }}
            inner = part[2:-2].strip()
            tokens.append(Token(TokenType.VAR, inner))

        elif part.startswith("{%") and part.endswith("%}"):
            # Block tag: {% for ... %} or {% endfor %}
            inner = part[2:-2].strip()

            if inner == "endfor":
                tokens.append(Token(TokenType.ENDFOR, ""))
            elif inner.startswith("for "):
                # Parse: for <loop_var> in <items_var>
                # e.g. "for item in items"
                m = re.match(r"^for\s+(\w+)\s+in\s+(\S+)$", inner)
                if m:
                    loop_var = m.group(1)
                    items_var = m.group(2)
                    tokens.append(Token(TokenType.FOR, f"{loop_var}|{items_var}"))
                else:
                    # Malformed for tag — treat as text
                    tokens.append(Token(TokenType.TEXT, part))
            else:
                # Unknown block tag — treat as text
                tokens.append(Token(TokenType.TEXT, part))

        else:
            # Plain text
            tokens.append(Token(TokenType.TEXT, part))

    return tokens
