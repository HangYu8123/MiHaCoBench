"""lexer.py — Tokenize a template string for the template engine.

Tokens types:
  TEXT    — literal text (no tags)
  VAR     — {{ varname }} or {{ a.b }}
  FOR     — {% for loop_var in items_var %}
  ENDFOR  — {% endfor %}
"""
from __future__ import annotations

import re


class TokenType:
    TEXT   = "TEXT"
    VAR    = "VAR"
    FOR    = "FOR"
    ENDFOR = "ENDFOR"


class Token:
    """A single lexer token."""

    __slots__ = ("type", "value")

    def __init__(self, type_: str, value: str) -> None:
        self.type  = type_
        self.value = value

    def __repr__(self) -> str:  # pragma: no cover
        return f"Token({self.type!r}, {self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self.type == other.type and self.value == other.value


# Match any {{ ... }} or {% ... %} tag; capture the inner content.
_TAG_RE = re.compile(r"(\{\{.*?\}\}|\{%.*?%\})", re.DOTALL)
# Match a VAR tag: {{ expr }}
_VAR_RE = re.compile(r"^\{\{\s*([\w.]+)\s*\}\}$")
# Match a FOR tag: {% for x in items %}
_FOR_RE = re.compile(r"^\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}$")
# Match an ENDFOR tag: {% endfor %}
_ENDFOR_RE = re.compile(r"^\{%\s*endfor\s*%\}$")


def tokenize(template: str) -> list[Token]:
    """Tokenize *template* into a list of :class:`Token` objects.

    Unrecognised tags are treated as literal TEXT.
    """
    tokens: list[Token] = []
    pos = 0
    for m in _TAG_RE.finditer(template):
        start, end = m.start(), m.end()
        if start > pos:
            tokens.append(Token(TokenType.TEXT, template[pos:start]))
        tag = m.group(1)
        if vm := _VAR_RE.match(tag):
            tokens.append(Token(TokenType.VAR, vm.group(1)))
        elif fm := _FOR_RE.match(tag):
            # value = "<loop_var>|<items_var>"
            tokens.append(Token(TokenType.FOR, f"{fm.group(1)}|{fm.group(2)}"))
        elif _ENDFOR_RE.match(tag):
            tokens.append(Token(TokenType.ENDFOR, ""))
        else:
            # Unknown tag → treat as literal text
            tokens.append(Token(TokenType.TEXT, tag))
        pos = end
    if pos < len(template):
        tokens.append(Token(TokenType.TEXT, template[pos:]))
    return tokens
