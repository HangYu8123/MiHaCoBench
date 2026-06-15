"""Broken parser for c04_formula_engine.

PLANTED DEFECT: all binary operators are given the same precedence (left-to-right
strict evaluation), so '2+3*4' evaluates as '(2+3)*4 = 20' instead of the
correct '2+(3*4) = 14'.  This breaks the operator-precedence tests in the grader.

Everything else is identical to the gold parser.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lexer import (
    Token, NUMBER, STRING, CELL, RANGE_SEP, OP, LPAREN, RPAREN, COMMA, EOF, tokenise
)


# ---------------------------------------------------------------------------
# AST node classes (identical to gold)
# ---------------------------------------------------------------------------

@dataclass
class NumLiteral:
    value: float


@dataclass
class StrLiteral:
    value: str


@dataclass
class CellRef:
    ref: str


@dataclass
class RangeRef:
    start: str
    end: str


@dataclass
class BinOp:
    op: str
    left: Any
    right: Any


@dataclass
class UnaryMinus:
    operand: Any


@dataclass
class FuncCall:
    name: str
    args: list = field(default_factory=list)


@dataclass
class IfExpr:
    cond_left: Any
    cond_op: str
    cond_right: Any
    true_expr: Any
    false_expr: Any


# ---------------------------------------------------------------------------
# BUG: all operators get the same precedence (1, 1) → strict left-to-right.
# ---------------------------------------------------------------------------

_INFIX_BP: dict[str, tuple[int, int]] = {
    "+": (1, 1),   # correct
    "-": (1, 1),   # correct
    "*": (1, 1),   # BUG: should be (2, 2)
    "/": (1, 1),   # BUG: should be (2, 2)
    "^": (1, 1),   # BUG: should be (4, 3)
}

_FUNC_NAMES = {"SUM", "AVG", "MIN", "MAX", "IF"}
_CMP_OPS = {"=", "<>", "<", "<=", ">", ">="}


class Parser:
    """Consume a token list and build an AST (broken precedence)."""

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, kind: str, value: str | None = None) -> Token:
        tok = self._advance()
        if tok.kind != kind:
            raise SyntaxError(
                f"Expected token kind {kind!r}, got {tok.kind!r} ({tok.value!r})"
            )
        if value is not None and tok.value != value:
            raise SyntaxError(
                f"Expected token value {value!r}, got {tok.value!r}"
            )
        return tok

    def _nud(self) -> Any:
        tok = self._advance()

        if tok.kind == NUMBER:
            return NumLiteral(tok.value)

        if tok.kind == STRING:
            return StrLiteral(tok.value)

        if tok.kind == CELL:
            return CellRef(tok.value)

        if tok.kind == LPAREN:
            node = self._parse_expr(0)
            self._expect(RPAREN)
            return node

        if tok.kind == OP and tok.value == "-":
            operand = self._parse_expr(5)
            return UnaryMinus(operand)

        if tok.kind == OP and tok.value in _FUNC_NAMES:
            return self._parse_func(tok.value)

        raise SyntaxError(
            f"Unexpected token {tok.kind!r} ({tok.value!r}) at pos {tok.pos}"
        )

    def _led(self, left: Any, op_tok: Token) -> Any:
        bp_left, bp_right = _INFIX_BP[op_tok.value]
        right = self._parse_expr(bp_right)
        return BinOp(op_tok.value, left, right)

    def _parse_expr(self, min_bp: int) -> Any:
        left = self._nud()

        while True:
            peek = self._peek()
            if peek.kind == EOF:
                break
            if peek.kind != OP or peek.value not in _INFIX_BP:
                break
            bp_left, _ = _INFIX_BP[peek.value]
            if bp_left <= min_bp:
                break
            op_tok = self._advance()
            left = self._led(left, op_tok)

        return left

    def _parse_arg(self) -> Any:
        peek = self._peek()
        if peek.kind == CELL:
            if self._pos + 1 < len(self._tokens):
                next_tok = self._tokens[self._pos + 1]
                if next_tok.kind == RANGE_SEP:
                    start = self._advance().value
                    self._advance()
                    end = self._expect(CELL).value
                    return RangeRef(start, end)
        return self._parse_expr(0)

    def _parse_func(self, name: str) -> Any:
        self._expect(LPAREN)
        if name == "IF":
            return self._parse_if()
        args = []
        if self._peek().kind != RPAREN:
            args.append(self._parse_arg())
            while self._peek().kind == COMMA:
                self._advance()
                args.append(self._parse_arg())
        self._expect(RPAREN)
        return FuncCall(name, args)

    def _parse_if(self) -> IfExpr:
        cond_left = self._parse_expr(0)
        cmp_tok = self._advance()
        if cmp_tok.kind != OP or cmp_tok.value not in _CMP_OPS:
            raise SyntaxError(
                f"Expected comparison operator in IF condition, "
                f"got {cmp_tok.kind!r} ({cmp_tok.value!r})"
            )
        cond_right = self._parse_expr(0)
        self._expect(COMMA)
        true_expr = self._parse_arg()
        self._expect(COMMA)
        false_expr = self._parse_arg()
        self._expect(RPAREN)
        return IfExpr(cond_left, cmp_tok.value, cond_right, true_expr, false_expr)

    def parse(self) -> Any:
        node = self._parse_expr(0)
        if self._peek().kind != EOF:
            tok = self._peek()
            raise SyntaxError(
                f"Unexpected token after expression: {tok.kind!r} ({tok.value!r})"
            )
        return node


def parse_formula(formula: str) -> Any:
    """Tokenise and parse *formula* (without the leading '='). Return AST root."""
    tokens = tokenise(formula)
    return Parser(tokens).parse()
