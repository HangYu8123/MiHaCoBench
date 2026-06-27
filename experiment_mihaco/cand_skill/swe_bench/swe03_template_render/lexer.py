"""lexer.py — Tokenizer for the minimal template engine."""

import re


class TokenType:
    TEXT   = "TEXT"
    VAR    = "VAR"
    FOR    = "FOR"
    ENDFOR = "ENDFOR"


class Token:
    """A single lexer token.

    Attributes
    ----------
    type  : str  — one of TokenType.*
    value : str  — TEXT=literal text, VAR=dotted path, FOR="loop_var|items_var"
    """

    __slots__ = ("type", "value")

    def __init__(self, type: str, value: str) -> None:  # noqa: A002
        self.type  = type
        self.value = value

    def __repr__(self) -> str:  # pragma: no cover
        return f"Token(type={self.type!r}, value={self.value!r})"


# Splits the template into alternating TEXT / TAG segments.
# The capturing group keeps the delimiters inside the result list.
_SPLIT_RE = re.compile(r"({{.*?}}|{%.*?%})", re.DOTALL)

# Match a VAR tag and capture the inner expression (stripped).
_VAR_RE   = re.compile(r"^\{\{\s*(.*?)\s*\}\}$", re.DOTALL)

# Match a FOR tag and capture loop_var + items_var.
_FOR_RE   = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}", re.DOTALL)

# Match an ENDFOR tag.
_ENDFOR_RE = re.compile(r"\{%\s*endfor\s*%\}", re.DOTALL)


def tokenize(template: str) -> list:
    """Return an ordered list of Token objects for *template*."""
    tokens: list = []

    for part in re.split(_SPLIT_RE, template):
        if not part:
            continue

        var_m = _VAR_RE.match(part)
        if var_m:
            tokens.append(Token(TokenType.VAR, var_m.group(1)))
            continue

        for_m = _FOR_RE.match(part)
        if for_m:
            loop_var, items_var = for_m.group(1), for_m.group(2)
            tokens.append(Token(TokenType.FOR, f"{loop_var}|{items_var}"))
            continue

        if _ENDFOR_RE.match(part):
            tokens.append(Token(TokenType.ENDFOR, ""))
            continue

        # Plain text (possibly the empty string between adjacent tags — keep
        # only non-empty stretches to avoid cluttering the token list).
        tokens.append(Token(TokenType.TEXT, part))

    return tokens
