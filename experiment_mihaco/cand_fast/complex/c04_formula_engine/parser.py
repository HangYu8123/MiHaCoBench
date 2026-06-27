"""Recursive-descent parser that builds an AST from a token list."""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from lexer import (
    Token, TT_NUMBER, TT_STRING, TT_RANGE, TT_IDENT,
    TT_OP, TT_COMPARE, TT_LPAREN, TT_RPAREN, TT_COMMA, TT_EOF,
)


# ---------------------------------------------------------------------------
# AST node definitions
# ---------------------------------------------------------------------------

@dataclass
class Num:
    val: float


@dataclass
class Str:
    val: str


@dataclass
class CellRef:
    ref: str


@dataclass
class Range:
    start: str
    end: str


@dataclass
class BinOp:
    op: str
    left: Any
    right: Any


@dataclass
class FuncCall:
    name: str
    args: List[Any]


@dataclass
class IfExpr:
    cond_op: str
    left: Any
    right: Any
    true_val: Any
    false_val: Any


# ---------------------------------------------------------------------------
# Precedence / associativity tables
# ---------------------------------------------------------------------------

_PREC = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
_RIGHT_ASSOC = {'^'}
_COMPARE_OPS = {'=', '<>', '<', '<=', '>', '>='}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self, expected_type: Optional[str] = None) -> Token:
        tok = self._tokens[self._pos]
        if expected_type is not None and tok.type != expected_type:
            raise SyntaxError(
                f"Expected {expected_type} but got {tok.type}={tok.value!r}"
            )
        self._pos += 1
        return tok

    # ------------------------------------------------------------------
    # Primary expression
    # ------------------------------------------------------------------

    def _parse_primary(self) -> Any:
        tok = self._peek()

        # Unary minus
        if tok.type == TT_OP and tok.value == '-':
            self._consume()
            operand = self._parse_primary()
            return BinOp('-', Num(0.0), operand)

        # Parenthesised expression
        if tok.type == TT_LPAREN:
            self._consume(TT_LPAREN)
            node = self._parse_expr(1)
            self._consume(TT_RPAREN)
            return node

        # Number literal
        if tok.type == TT_NUMBER:
            self._consume()
            return Num(float(tok.value))

        # String literal (strip surrounding double-quotes)
        if tok.type == TT_STRING:
            self._consume()
            return Str(tok.value[1:-1])

        # Range literal (must be checked before IDENT since both match uppercase)
        if tok.type == TT_RANGE:
            self._consume()
            start, end = tok.value.split(':')
            return Range(start, end)

        # Identifier: either a function call or a cell reference
        if tok.type == TT_IDENT:
            self._consume()
            name = tok.value

            # Function call?
            if self._peek().type == TT_LPAREN:
                return self._parse_func_call(name)

            # Cell reference: uppercase letters followed by digits
            import re
            if re.fullmatch(r'[A-Z]+\d+', name):
                return CellRef(name)

            raise SyntaxError(f"Unknown identifier: {name!r}")

        raise SyntaxError(f"Unexpected token {tok.type}={tok.value!r}")

    # ------------------------------------------------------------------
    # Function call (already consumed the function name)
    # ------------------------------------------------------------------

    def _parse_func_call(self, name: str) -> Any:
        upper = name.upper()
        self._consume(TT_LPAREN)

        if upper == 'IF':
            return self._parse_if()

        # Aggregate functions: SUM, AVG, MIN, MAX, or generic
        args = self._parse_arg_list()
        self._consume(TT_RPAREN)
        return FuncCall(upper, args)

    def _parse_if(self) -> IfExpr:
        """Parse IF(condition, true_val, false_val)."""
        # condition is: left_expr  compare_op  right_expr
        left = self._parse_expr(1)
        cmp_tok = self._peek()
        if cmp_tok.type != TT_COMPARE:
            raise SyntaxError(
                f"Expected comparison operator in IF condition, got {cmp_tok.type}={cmp_tok.value!r}"
            )
        self._consume()
        cond_op = cmp_tok.value
        right = self._parse_expr(1)

        self._consume(TT_COMMA)
        true_val = self._parse_expr(1)
        self._consume(TT_COMMA)
        false_val = self._parse_expr(1)
        self._consume(TT_RPAREN)

        return IfExpr(cond_op, left, right, true_val, false_val)

    def _parse_arg_list(self) -> List[Any]:
        """Parse comma-separated list of arguments."""
        args: List[Any] = []
        if self._peek().type == TT_RPAREN:
            return args
        args.append(self._parse_expr(1))
        while self._peek().type == TT_COMMA:
            self._consume(TT_COMMA)
            args.append(self._parse_expr(1))
        return args

    # ------------------------------------------------------------------
    # Binary expression with precedence climbing
    # ------------------------------------------------------------------

    def _parse_expr(self, min_prec: int) -> Any:
        left = self._parse_primary()

        while True:
            tok = self._peek()
            if tok.type != TT_OP:
                break
            op = tok.value
            prec = _PREC.get(op)
            if prec is None or prec < min_prec:
                break
            self._consume()
            next_min = prec if op in _RIGHT_ASSOC else prec + 1
            right = self._parse_expr(next_min)
            left = BinOp(op, left, right)

        return left

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def parse(self) -> Any:
        node = self._parse_expr(1)
        if self._peek().type != TT_EOF:
            tok = self._peek()
            raise SyntaxError(f"Unexpected token after expression: {tok.type}={tok.value!r}")
        return node


def parse(tokens) -> Any:
    """Public entry point: parse a token list into an AST."""
    return Parser(tokens).parse()
