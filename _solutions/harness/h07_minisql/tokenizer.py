"""Tokenizer for the mini-SQL dialect (gold reference).

Turns a raw SQL statement string into a flat list of :class:`Token` objects.
Keyword recognition is **case-insensitive** (the token's canonical ``value`` for
a keyword is upper-cased), while identifiers and string literals keep their
original case.

Token kinds
-----------
``KW``      reserved keyword (value upper-cased, e.g. ``SELECT``)
``IDENT``   identifier (table/column name, original case)
``INT``     integer literal (value is a Python ``int``)
``STR``     single-quoted string literal (value is the decoded ``str``; ``''``
            inside the quotes is an escaped single quote)
``NULL``    the literal ``NULL``
``STAR``    ``*``
``COMMA``   ``,``
``LPAREN``  ``(``
``RPAREN``  ``)``
``OP``      a comparison operator: ``=`` ``<>`` ``<`` ``<=`` ``>`` ``>=``
``EOF``     end-of-input sentinel

Any character that cannot start one of the above raises :class:`ValueError`,
which the engine surfaces as the contract's "malformed statement" error.
"""
from __future__ import annotations

from dataclasses import dataclass


KW = "KW"
IDENT = "IDENT"
INT = "INT"
STR = "STR"
NULL = "NULL"
STAR = "STAR"
COMMA = "COMMA"
LPAREN = "LPAREN"
RPAREN = "RPAREN"
OP = "OP"
EOF = "EOF"


# Reserved keywords. NULL is handled as its own token kind, but listed here so
# it is never mistaken for an identifier.
_KEYWORDS = {
    "SELECT", "DISTINCT", "FROM", "WHERE", "GROUP", "BY", "ORDER", "LIMIT",
    "OFFSET", "AS", "AND", "OR", "NOT", "IS", "ASC", "DESC",
    "CREATE", "TABLE", "INSERT", "INTO", "VALUES",
    "INT", "TEXT",
    "COUNT", "SUM", "AVG", "MIN", "MAX",
}


@dataclass(frozen=True)
class Token:
    kind: str
    value: object  # str for most kinds; int for INT; None for NULL


def tokenize(sql: str) -> list[Token]:
    """Return the list of tokens for ``sql`` (always ending with an ``EOF``)."""
    tokens: list[Token] = []
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        # Whitespace is insignificant.
        if ch.isspace():
            i += 1
            continue
        # Punctuation / operators.
        if ch == ",":
            tokens.append(Token(COMMA, ","))
            i += 1
            continue
        if ch == "(":
            tokens.append(Token(LPAREN, "("))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token(RPAREN, ")"))
            i += 1
            continue
        if ch == "*":
            tokens.append(Token(STAR, "*"))
            i += 1
            continue
        # Two-char operators must be matched before their single-char prefixes.
        two = sql[i:i + 2]
        if two in ("<>", "<=", ">="):
            tokens.append(Token(OP, two))
            i += 2
            continue
        if ch in "=<>":
            tokens.append(Token(OP, ch))
            i += 1
            continue
        # String literal: single-quoted, '' is an escaped quote.
        if ch == "'":
            i += 1
            buf: list[str] = []
            closed = False
            while i < n:
                c = sql[i]
                if c == "'":
                    if i + 1 < n and sql[i + 1] == "'":  # escaped quote
                        buf.append("'")
                        i += 2
                        continue
                    closed = True
                    i += 1
                    break
                buf.append(c)
                i += 1
            if not closed:
                raise ValueError("unterminated string literal")
            tokens.append(Token(STR, "".join(buf)))
            continue
        # Integer literal (optionally signed). A leading '-' is only an integer
        # literal when followed by a digit; otherwise it is not part of this
        # dialect and is rejected here.
        if ch.isdigit() or (ch == "-" and i + 1 < n and sql[i + 1].isdigit()):
            j = i + 1 if ch == "-" else i
            while j < n and sql[j].isdigit():
                j += 1
            tokens.append(Token(INT, int(sql[i:j])))
            i = j
            continue
        # Identifier or keyword: [A-Za-z_][A-Za-z0-9_]*
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
            word = sql[i:j]
            upper = word.upper()
            if upper == "NULL":
                tokens.append(Token(NULL, None))
            elif upper in _KEYWORDS:
                tokens.append(Token(KW, upper))
            else:
                tokens.append(Token(IDENT, word))
            i = j
            continue
        raise ValueError(f"unexpected character {ch!r} in statement")
    tokens.append(Token(EOF, None))
    return tokens
