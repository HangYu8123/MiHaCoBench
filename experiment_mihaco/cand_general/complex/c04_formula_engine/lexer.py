"""
lexer.py — Tokenizer for the mini spreadsheet formula language.

Token types:
  NUMBER    : numeric literal (int or float)
  STRING    : double-quoted string literal
  RANGE     : cell range like A1:B3 (matched before CELL_REF)
  CELL_REF  : single cell reference like A1, AA10
  FUNC_NAME : one of SUM, AVG, MIN, MAX, IF
  OP        : arithmetic operator + - * / ^
  CMP       : comparison operator <= >= <> < > =
  LPAREN    : (
  RPAREN    : )
  COMMA     : ,
"""

import re
from collections import namedtuple

Token = namedtuple("Token", ["type", "value"])

# Order matters: RANGE before CELL_REF, multi-char CMP before single-char
_TOKEN_PATTERN = re.compile(
    r'(?P<NUMBER>[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)'
    r'|(?P<STRING>"[^"]*")'
    r'|(?P<RANGE>[A-Z]+[0-9]+:[A-Z]+[0-9]+)'
    r'|(?P<FUNC_NAME>(?:SUM|AVG|MIN|MAX|IF)(?=[(\s]))'
    r'|(?P<CELL_REF>[A-Z]+[0-9]+)'
    r'|(?P<CMP><=|>=|<>|<|>|=)'
    r'|(?P<OP>[+\-*/^])'
    r'|(?P<LPAREN>\()'
    r'|(?P<RPAREN>\))'
    r'|(?P<COMMA>,)'
    r'|(?P<SKIP>\s+)'
)


def tokenize(formula: str) -> list[Token]:
    """
    Tokenize a formula string (without the leading '=').

    Returns a list of Token namedtuples. Raises SyntaxError for unknown chars.
    Note: '-' is always emitted as OP; unary minus is handled by the parser.
    We do NOT want the NUMBER pattern to consume leading sign here,
    because '-' in context like '3 - 2' or '-A1' needs different treatment.
    """
    tokens = []
    pos = 0
    text = formula

    # We use a simpler approach: match token by token, but treat '-'/'+' as OPs
    # The NUMBER group above would match signed numbers; we want to be careful.
    # We'll use a pattern that does NOT include sign in NUMBER, and let '-' be OP.
    for match in _UNSIGNED_TOKEN_PATTERN.finditer(text):
        kind = match.lastgroup
        value = match.group()
        if kind == "SKIP":
            continue
        tokens.append(Token(kind, value))

    return tokens


# Redefine without sign in NUMBER to ensure '-' is always OP
_UNSIGNED_TOKEN_PATTERN = re.compile(
    r'(?P<NUMBER>\d+\.?\d*|\.\d+)'
    r'|(?P<STRING>"[^"]*")'
    r'|(?P<RANGE>[A-Z]+[0-9]+:[A-Z]+[0-9]+)'
    r'|(?P<FUNC_NAME>(?:SUM|AVG|MIN|MAX|IF)(?=[(\s,)]))'
    r'|(?P<CELL_REF>[A-Z]+[0-9]+)'
    r'|(?P<CMP><=|>=|<>|<|>|=)'
    r'|(?P<OP>[+\-*/^])'
    r'|(?P<LPAREN>\()'
    r'|(?P<RPAREN>\))'
    r'|(?P<COMMA>,)'
    r'|(?P<SKIP>\s+)'
)
