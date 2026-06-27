"""
lexer.py — Tokenizer for the spreadsheet formula engine.

Token types: NUMBER, STRING, IDENT, RANGE, OP, EOF.
"""

import re
from typing import List, NamedTuple


class Token(NamedTuple):
    type: str
    value: str


# Token specification — ORDER MATTERS for alternation (longest match first).
# RANGE must come before IDENT and OP to avoid ':' being swallowed separately.
# Multi-char OPs (<=, >=, <>) must come before single-char OPs.
_TOKEN_SPEC = [
    ('RANGE',   r'[A-Z]+\d+:[A-Z]+\d+'),          # e.g. A1:B3
    ('NUMBER',  r'\d+(\.\d*)?'),                    # e.g. 3, 3.14 (NO leading -)
    ('STRING',  r'"[^"]*"'),                        # e.g. "hello"
    ('IDENT',   r'[A-Z]+\d*'),                      # cell refs (A1) and function names (SUM)
    ('OP',      r'<=|>=|<>|[+\-*/^(),=<>]'),        # operators and punctuation
    ('SKIP',    r'\s+'),                             # whitespace (discarded)
]

_MASTER_RE = re.compile(
    '|'.join('(?P<%s>%s)' % (name, pattern) for name, pattern in _TOKEN_SPEC)
)


def tokenize(formula: str) -> List[Token]:
    """
    Tokenize a formula string. If it starts with '=', strip that prefix first.

    Returns a list of Token objects ending with an EOF token.
    """
    text = formula.lstrip()
    if text.startswith('='):
        text = text[1:]

    tokens: List[Token] = []
    for mo in _MASTER_RE.finditer(text):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP':
            continue
        if kind == 'NUMBER':
            # Strip capturing group — just keep the full match
            tokens.append(Token('NUMBER', value))
        else:
            tokens.append(Token(kind, value))

    tokens.append(Token('EOF', ''))
    return tokens
