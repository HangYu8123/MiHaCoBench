"""Lexer for the spreadsheet formula language."""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    type: str
    value: str


# Token types
TT_NUMBER = 'NUMBER'
TT_STRING = 'STRING'
TT_RANGE = 'RANGE'
TT_IDENT = 'IDENT'
TT_OP = 'OP'
TT_COMPARE = 'COMPARE'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_COMMA = 'COMMA'
TT_EOF = 'EOF'

# Regex patterns — order matters: longer/more-specific first
_TOKEN_PATTERNS = [
    (TT_RANGE,   r'[A-Z]+\d+:[A-Z]+\d+'),
    (TT_NUMBER,  r'\d+(?:\.\d+)?'),
    (TT_STRING,  r'"[^"]*"'),
    (TT_IDENT,   r'[A-Z]+\d+|[A-Za-z_][A-Za-z0-9_]*'),
    (TT_COMPARE, r'<>|<=|>=|<|>|='),
    (TT_OP,      r'[+\-*/^]'),
    (TT_LPAREN,  r'\('),
    (TT_RPAREN,  r'\)'),
    (TT_COMMA,   r','),
]

_MASTER_RE = re.compile(
    '|'.join(f'(?P<{name}>{pat})' for name, pat in _TOKEN_PATTERNS)
)


def lex(formula: str) -> List[Token]:
    """Tokenize a formula string (without the leading '=')."""
    tokens: List[Token] = []
    pos = 0
    s = formula.strip()
    while pos < len(s):
        if s[pos] == ' ':
            pos += 1
            continue
        m = _MASTER_RE.match(s, pos)
        if m is None:
            raise SyntaxError(f"Unexpected character {s[pos]!r} at position {pos}")
        ttype = m.lastgroup
        tvalue = m.group()
        tokens.append(Token(ttype, tvalue))
        pos = m.end()
    tokens.append(Token(TT_EOF, ''))
    return tokens
