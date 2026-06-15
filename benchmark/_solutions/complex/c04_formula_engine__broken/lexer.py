"""Lexer for the formula engine.

Tokenises a formula string (without the leading '=') into a flat list of
Token objects.  Token types:

    NUMBER    — float literal
    STRING    — double-quoted string literal (content without quotes)
    CELL      — cell reference like A1, B2, AA10
    RANGE_SEP — the ':' separator in a range expression (A1:B3)
    OP        — single arithmetic or comparison operator character/pair
    LPAREN    — '('
    RPAREN    — ')'
    COMMA     — ','
    EOF       — sentinel end token
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Token definition
# ---------------------------------------------------------------------------

NUMBER = "NUMBER"
STRING = "STRING"
CELL = "CELL"
RANGE_SEP = "RANGE_SEP"
OP = "OP"
LPAREN = "LPAREN"
RPAREN = "RPAREN"
COMMA = "COMMA"
EOF = "EOF"

# Two-character comparison operators must be tried before their single-char
# prefixes so that '<=' is not tokenised as '<' then '='.
_TWO_CHAR_OPS = {"<>", "<=", ">="}
_ONE_CHAR_OPS = set("+-*/^=<>")


@dataclass
class Token:
    """A single lexical unit."""
    kind: str
    value: str | float
    pos: int  # offset in the original formula string


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

_CELL_RE = re.compile(r"([A-Z]+)([0-9]+)")
_NUM_RE = re.compile(r"[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?")


def tokenise(formula: str) -> list[Token]:
    """Return all tokens for *formula* (without the leading '=').

    Whitespace is silently skipped.  Raises ``SyntaxError`` on unrecognised
    input.
    """
    tokens: list[Token] = []
    i = 0
    n = len(formula)

    while i < n:
        ch = formula[i]

        # Skip whitespace.
        if ch.isspace():
            i += 1
            continue

        # String literal.
        if ch == '"':
            j = i + 1
            while j < n and formula[j] != '"':
                j += 1
            if j >= n:
                raise SyntaxError(f"Unterminated string at position {i}")
            tokens.append(Token(STRING, formula[i + 1:j], i))
            i = j + 1
            continue

        # Number literal.
        m = _NUM_RE.match(formula, i)
        if m:
            tokens.append(Token(NUMBER, float(m.group()), i))
            i = m.end()
            continue

        # Uppercase letter(s) → could be a cell reference or a function name.
        if ch.isupper():
            j = i
            while j < n and formula[j].isupper():
                j += 1
            word = formula[i:j]
            # If followed by digits it's a cell ref; otherwise a function/keyword.
            if j < n and formula[j].isdigit():
                k = j
                while k < n and formula[k].isdigit():
                    k += 1
                tokens.append(Token(CELL, formula[i:k], i))
                i = k
            else:
                # Treat as an OP-like identifier (function name handled by parser).
                tokens.append(Token(OP, word, i))
                i = j
            continue

        # Two-character operator.
        if i + 1 < n and formula[i:i + 2] in _TWO_CHAR_OPS:
            tokens.append(Token(OP, formula[i:i + 2], i))
            i += 2
            continue

        # One-character operator.
        if ch in _ONE_CHAR_OPS:
            tokens.append(Token(OP, ch, i))
            i += 1
            continue

        # Structural punctuation.
        if ch == "(":
            tokens.append(Token(LPAREN, "(", i))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token(RPAREN, ")", i))
            i += 1
            continue
        if ch == ",":
            tokens.append(Token(COMMA, ",", i))
            i += 1
            continue
        if ch == ":":
            tokens.append(Token(RANGE_SEP, ":", i))
            i += 1
            continue

        # Negative sign before a number (unary minus).
        if ch == "-":
            tokens.append(Token(OP, "-", i))
            i += 1
            continue

        raise SyntaxError(f"Unexpected character {ch!r} at position {i}")

    tokens.append(Token(EOF, "", n))
    return tokens
