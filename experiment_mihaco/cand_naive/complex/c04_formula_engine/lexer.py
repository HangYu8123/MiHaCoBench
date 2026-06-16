"""
lexer.py — Tokenizer for the spreadsheet formula language.
"""

import re
from enum import Enum, auto
from typing import List, NamedTuple


class TokenType(Enum):
    NUMBER = auto()
    STRING = auto()       # double-quoted string literal
    CELL_REF = auto()     # e.g. A1, B2, AA10
    RANGE = auto()        # e.g. A1:B3
    FUNC = auto()         # SUM, AVG, MIN, MAX, IF
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EQ = auto()           # = (comparison inside IF)
    NEQ = auto()          # <>
    LT = auto()           # <
    LTE = auto()          # <=
    GT = auto()           # >
    GTE = auto()          # >=
    EOF = auto()


class Token(NamedTuple):
    type: TokenType
    value: object  # str | float


FUNCTIONS = {"SUM", "AVG", "MIN", "MAX", "IF"}

# Regex patterns (order matters)
_TOKEN_RE = re.compile(
    r"""
    (?P<NUMBER>  -?(?:\d+\.\d*|\.\d+|\d+)  )   |  # number (int or float)
    "(?P<STRING> [^"]*                      )"  |  # double-quoted string
    (?P<FUNCREF> [A-Z]+(?:\d+:[A-Z]+\d+|(?=\())? )  |  # func name or cell ref
    (?P<NEQ>     <>                         )   |
    (?P<LTE>     <=                         )   |
    (?P<GTE>     >=                         )   |
    (?P<LT>      <                          )   |
    (?P<GT>      >                          )   |
    (?P<EQ>      =                          )   |
    (?P<PLUS>    \+                         )   |
    (?P<MINUS>   -                          )   |
    (?P<STAR>    \*                         )   |
    (?P<SLASH>   /                          )   |
    (?P<CARET>   \^                         )   |
    (?P<LPAREN>  \(                         )   |
    (?P<RPAREN>  \)                         )   |
    (?P<COMMA>   ,                          )   |
    (?P<WS>      \s+                        )       # whitespace to skip
    """,
    re.VERBOSE,
)

# Better pattern — split out cell range vs cell ref vs function name
_RANGE_RE = re.compile(r'^([A-Z]+\d+):([A-Z]+\d+)$')
_CELLREF_RE = re.compile(r'^[A-Z]+\d+$')


def tokenize(formula: str) -> List[Token]:
    """
    Tokenize a formula string (without the leading '=').
    Returns a list of Token objects terminated by EOF.
    """
    tokens: List[Token] = []
    pos = 0
    n = len(formula)

    while pos < n:
        # Skip whitespace
        if formula[pos].isspace():
            pos += 1
            continue

        # Try to match a double-quoted string
        if formula[pos] == '"':
            end = formula.find('"', pos + 1)
            if end == -1:
                raise SyntaxError(f"Unterminated string at position {pos}")
            tokens.append(Token(TokenType.STRING, formula[pos + 1:end]))
            pos = end + 1
            continue

        # Two-char operators
        two = formula[pos:pos+2]
        if two == '<>':
            tokens.append(Token(TokenType.NEQ, '<>'))
            pos += 2
            continue
        if two == '<=':
            tokens.append(Token(TokenType.LTE, '<='))
            pos += 2
            continue
        if two == '>=':
            tokens.append(Token(TokenType.GTE, '>='))
            pos += 2
            continue

        # Single-char operators/punctuation
        c = formula[pos]
        single_map = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '^': TokenType.CARET,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            ',': TokenType.COMMA,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '=': TokenType.EQ,
        }
        if c in single_map:
            tokens.append(Token(single_map[c], c))
            pos += 1
            continue

        # Number: optional minus then digits/dot
        num_match = re.match(r'-?(?:\d+\.\d*|\.\d+|\d+)', formula[pos:])
        if num_match and (c.isdigit() or (c == '-' and pos + 1 < n and formula[pos+1].isdigit())):
            tokens.append(Token(TokenType.NUMBER, float(num_match.group())))
            pos += len(num_match.group())
            continue

        # Identifier: uppercase letters then possibly digits (cell ref or function name)
        # Also handle ranges like A1:B3
        if c.isupper():
            # Greedily read letters
            letters_end = pos
            while letters_end < n and formula[letters_end].isupper():
                letters_end += 1
            word = formula[pos:letters_end]

            # Check if it's a known function
            if word in FUNCTIONS and letters_end < n and formula[letters_end] == '(':
                tokens.append(Token(TokenType.FUNC, word))
                pos = letters_end
                continue

            # Read digits for cell ref
            digits_end = letters_end
            while digits_end < n and formula[digits_end].isdigit():
                digits_end += 1
            cell_ref = formula[pos:digits_end]

            # Check for range: A1:B3
            if digits_end < n and formula[digits_end] == ':':
                # Try to read second cell ref
                colon_pos = digits_end
                letters2_end = colon_pos + 1
                while letters2_end < n and formula[letters2_end].isupper():
                    letters2_end += 1
                digits2_end = letters2_end
                while digits2_end < n and formula[digits2_end].isdigit():
                    digits2_end += 1
                cell_ref2 = formula[colon_pos + 1:digits2_end]
                if _CELLREF_RE.match(cell_ref) and _CELLREF_RE.match(cell_ref2):
                    tokens.append(Token(TokenType.RANGE, f"{cell_ref}:{cell_ref2}"))
                    pos = digits2_end
                    continue

            # It's a cell reference
            if _CELLREF_RE.match(cell_ref):
                tokens.append(Token(TokenType.CELL_REF, cell_ref))
                pos = digits_end
                continue

            raise SyntaxError(f"Unexpected identifier '{word}' at position {pos}")

        # Number starting with digit (no leading minus)
        if c.isdigit():
            num_match2 = re.match(r'\d+\.\d*|\d+', formula[pos:])
            if num_match2:
                tokens.append(Token(TokenType.NUMBER, float(num_match2.group())))
                pos += len(num_match2.group())
                continue

        raise SyntaxError(f"Unexpected character {c!r} at position {pos}")

    tokens.append(Token(TokenType.EOF, None))
    return tokens
