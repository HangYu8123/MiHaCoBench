"""
lexer.py — Tokenizer for the mini spreadsheet formula language.
"""

import re
from enum import Enum, auto


class TType(Enum):
    NUMBER   = auto()
    STRING   = auto()   # double-quoted string literal
    REF      = auto()   # cell reference like A1, AA10
    RANGE    = auto()   # A1:B3
    FUNC     = auto()   # SUM, AVG, MIN, MAX, IF
    PLUS     = auto()
    MINUS    = auto()
    STAR     = auto()
    SLASH    = auto()
    CARET    = auto()
    LPAREN   = auto()
    RPAREN   = auto()
    COMMA    = auto()
    EQ       = auto()   # =   (comparison inside IF)
    NEQ      = auto()   # <>
    LT       = auto()   # <
    LE       = auto()   # <=
    GT       = auto()   # >
    GE       = auto()   # >=
    EOF      = auto()


class Token:
    __slots__ = ("type", "value")

    def __init__(self, type_: TType, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


_FUNCTIONS = {"SUM", "AVG", "MIN", "MAX", "IF"}

# Regex pieces
_NUM_RE  = re.compile(r"-?(?:\d+\.?\d*|\.\d+)")
_REF_RE  = re.compile(r"([A-Z]+)(\d+)")
_FUNC_RE = re.compile(r"[A-Z]+")
_STR_RE  = re.compile(r'"([^"]*)"')


def tokenize(formula: str) -> list[Token]:
    """
    Tokenize a formula string (with the leading '=' already stripped).
    Returns a list of Token objects ending with TType.EOF.
    """
    tokens: list[Token] = []
    i = 0
    n = len(formula)

    while i < n:
        c = formula[i]

        # Skip whitespace
        if c in " \t\r\n":
            i += 1
            continue

        # Double-quoted string literal
        if c == '"':
            m = _STR_RE.match(formula, i)
            if m:
                tokens.append(Token(TType.STRING, m.group(1)))
                i = m.end()
                continue
            raise SyntaxError(f"Unterminated string at position {i}")

        # Number (may start with '-' only if not preceded by a number/ref token)
        # We handle unary minus in the parser; here only tokenize positive numbers
        # and let the parser deal with '-' as unary.
        if c.isdigit() or (c == '.' and i + 1 < n and formula[i+1].isdigit()):
            m = re.compile(r"\d+\.?\d*|\.\d+").match(formula, i)
            if m:
                tokens.append(Token(TType.NUMBER, float(m.group())))
                i = m.end()
                continue

        # Identifiers: functions or cell references
        if c.isupper():
            # Try function name first (must not be followed by digits directly meaning ref)
            m = _FUNC_RE.match(formula, i)
            word = m.group() if m else ""
            # Check if it's a cell reference (letters followed immediately by digits)
            ref_m = _REF_RE.match(formula, i)
            if ref_m and ref_m.group() == word + ref_m.group(2):
                # It IS a cell reference
                ref_str = ref_m.group()
                j = ref_m.end()
                # Check for range A1:B3
                if j < n and formula[j] == ':':
                    ref2_m = _REF_RE.match(formula, j + 1)
                    if ref2_m:
                        range_str = ref_str + ':' + ref2_m.group()
                        tokens.append(Token(TType.RANGE, range_str))
                        i = ref2_m.end()
                        continue
                tokens.append(Token(TType.REF, ref_str))
                i = j
                continue
            # It's a function/keyword
            if word in _FUNCTIONS:
                tokens.append(Token(TType.FUNC, word))
                i += len(word)
                continue
            raise SyntaxError(f"Unknown identifier '{word}' at position {i}")

        # Operators and punctuation
        if formula[i:i+2] == '<>':
            tokens.append(Token(TType.NEQ, '<>'))
            i += 2; continue
        if formula[i:i+2] == '<=':
            tokens.append(Token(TType.LE, '<='))
            i += 2; continue
        if formula[i:i+2] == '>=':
            tokens.append(Token(TType.GE, '>='))
            i += 2; continue

        _single = {
            '+': TType.PLUS,
            '-': TType.MINUS,
            '*': TType.STAR,
            '/': TType.SLASH,
            '^': TType.CARET,
            '(': TType.LPAREN,
            ')': TType.RPAREN,
            ',': TType.COMMA,
            '=': TType.EQ,
            '<': TType.LT,
            '>': TType.GT,
        }
        if c in _single:
            tokens.append(Token(_single[c], c))
            i += 1
            continue

        raise SyntaxError(f"Unexpected character '{c}' at position {i}")

    tokens.append(Token(TType.EOF, None))
    return tokens
