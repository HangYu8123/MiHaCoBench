"""evaluator.py — Formula tokenizer and recursive descent evaluator.

Supports formulas of the form:
    =A1+B2*2
    =(A1+B2)/C3
    =3.14*R1+0.5

Operator precedence:
    * and / bind tighter than + and -
    Parentheses override precedence.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple

# Token types
_TOK_NUM = "NUM"
_TOK_CELL = "CELL"
_TOK_OP = "OP"
_TOK_LPAREN = "LPAREN"
_TOK_RPAREN = "RPAREN"
_TOK_EOF = "EOF"

_CELL_RE = re.compile(r"^[A-Z]+[0-9]+$")


def tokenize(expr: str) -> List[Tuple[str, str]]:
    """Tokenize a formula string (with or without leading '=').

    Returns a list of (type, value) pairs.
    """
    s = expr.lstrip()
    if s.startswith("="):
        s = s[1:]

    tokens: List[Tuple[str, str]] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in " \t":
            i += 1
            continue
        if c in "+-*/":
            tokens.append((_TOK_OP, c))
            i += 1
        elif c == "(":
            tokens.append((_TOK_LPAREN, "("))
            i += 1
        elif c == ")":
            tokens.append((_TOK_RPAREN, ")"))
            i += 1
        elif c.isdigit() or (c == "." and i + 1 < len(s) and s[i + 1].isdigit()):
            # numeric literal
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] == "."):
                j += 1
            tokens.append((_TOK_NUM, s[i:j]))
            i = j
        elif c.isupper():
            # Could be a cell reference like A1, B2, AA10
            j = i
            while j < len(s) and s[j].isupper():
                j += 1
            while j < len(s) and s[j].isdigit():
                j += 1
            tok_val = s[i:j]
            if _CELL_RE.match(tok_val):
                tokens.append((_TOK_CELL, tok_val))
            else:
                raise ValueError(f"Unknown token in formula: {tok_val!r}")
            i = j
        else:
            raise ValueError(f"Unexpected character {c!r} in formula: {expr!r}")

    tokens.append((_TOK_EOF, ""))
    return tokens


def extract_cell_refs(expr: str) -> List[str]:
    """Return all cell references found in a formula expression."""
    tokens = tokenize(expr)
    return [val for (typ, val) in tokens if typ == _TOK_CELL]


class _Parser:
    """Recursive-descent parser for arithmetic expressions with cell refs."""

    def __init__(self, tokens: List[Tuple[str, str]], cell_value_fn: Callable[[str], float]) -> None:
        self._tokens = tokens
        self._pos = 0
        self._cell_value = cell_value_fn

    def _peek(self) -> Tuple[str, str]:
        return self._tokens[self._pos]

    def _consume(self, expected_type: Optional[str] = None) -> Tuple[str, str]:
        tok = self._tokens[self._pos]
        if expected_type and tok[0] != expected_type:
            raise ValueError(f"Expected {expected_type}, got {tok}")
        self._pos += 1
        return tok

    def parse(self) -> float:
        """Parse and evaluate the full expression."""
        val = self._parse_additive()
        if self._peek()[0] != _TOK_EOF:
            raise ValueError(f"Unexpected token: {self._peek()}")
        return val

    def _parse_additive(self) -> float:
        """Parse addition and subtraction (lowest precedence)."""
        left = self._parse_multiplicative()
        while self._peek()[0] == _TOK_OP and self._peek()[1] in ("+", "-"):
            op = self._consume(_TOK_OP)[1]
            right = self._parse_multiplicative()
            if op == "+":
                left += right
            else:
                left -= right
        return left

    def _parse_multiplicative(self) -> float:
        """Parse multiplication and division (higher precedence)."""
        left = self._parse_unary()
        while self._peek()[0] == _TOK_OP and self._peek()[1] in ("*", "/"):
            op = self._consume(_TOK_OP)[1]
            right = self._parse_unary()
            if op == "*":
                left *= right
            else:
                if right == 0.0:
                    raise ZeroDivisionError("Division by zero in formula")
                left /= right
        return left

    def _parse_unary(self) -> float:
        """Parse optional leading unary minus."""
        if self._peek()[0] == _TOK_OP and self._peek()[1] == "-":
            self._consume(_TOK_OP)
            return -self._parse_primary()
        if self._peek()[0] == _TOK_OP and self._peek()[1] == "+":
            self._consume(_TOK_OP)
            return self._parse_primary()
        return self._parse_primary()

    def _parse_primary(self) -> float:
        """Parse a number literal, cell reference, or parenthesised sub-expression."""
        tok_type, tok_val = self._peek()
        if tok_type == _TOK_NUM:
            self._consume()
            return float(tok_val)
        if tok_type == _TOK_CELL:
            self._consume()
            return self._cell_value(tok_val)
        if tok_type == _TOK_LPAREN:
            self._consume(_TOK_LPAREN)
            val = self._parse_additive()
            self._consume(_TOK_RPAREN)
            return val
        raise ValueError(f"Unexpected token in primary: {self._peek()}")


def evaluate_formula(expr: str, cell_value_fn: Callable[[str], float]) -> float:
    """Parse and evaluate a formula string using *cell_value_fn* to resolve references.

    Args:
        expr: Formula string, e.g. "=A1+B2*2" or "=(A1+B2)/3".
        cell_value_fn: Callable that maps a cell address string to its float value.

    Returns:
        The computed float result.
    """
    tokens = tokenize(expr)
    parser = _Parser(tokens, cell_value_fn)
    return parser.parse()
