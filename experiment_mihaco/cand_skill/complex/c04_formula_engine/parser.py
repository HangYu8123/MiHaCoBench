"""
parser.py — Recursive-descent parser for the spreadsheet formula engine.

AST node types:
  Literal(value: float)
  StrLiteral(value: str)
  CellRef(ref: str)
  Range(start: str, end: str)
  BinOp(op: str, left, right)
  UnaryMinus(expr)
  FuncCall(name: str, args: list)
  IfExpr(cond_op: str, lhs, rhs, true_branch, false_branch)

Precedence:
  Level 1 (lowest): +  -  (left-associative)
  Level 2:          *  /  (left-associative)
  Level 3 (highest): ^   (right-associative)
"""

from dataclasses import dataclass, field
from typing import Any, List

from lexer import Token, tokenize


# ---------------------------------------------------------------------------
# AST node definitions
# ---------------------------------------------------------------------------

@dataclass
class Literal:
    value: float


@dataclass
class StrLiteral:
    value: str


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
class UnaryMinus:
    expr: Any


@dataclass
class FuncCall:
    name: str
    args: List[Any] = field(default_factory=list)


@dataclass
class IfExpr:
    cond_op: str
    lhs: Any
    rhs: Any
    true_branch: Any
    false_branch: Any


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return Token('EOF', '')

    def _consume(self, expected_type: str = None, expected_value: str = None) -> Token:
        tok = self._current()
        if expected_type and tok.type != expected_type:
            raise SyntaxError(
                f"Expected token type {expected_type!r} but got {tok.type!r} ({tok.value!r})"
            )
        if expected_value and tok.value != expected_value:
            raise SyntaxError(
                f"Expected token value {expected_value!r} but got {tok.value!r}"
            )
        self._pos += 1
        return tok

    # ------------------------------------------------------------------
    # Grammar rules (lowest-to-highest precedence)
    # ------------------------------------------------------------------

    def parse_expr(self) -> Any:
        """Level 1: + and - (left-associative)."""
        left = self.parse_term()
        while self._current().type == 'OP' and self._current().value in ('+', '-'):
            op = self._consume('OP').value
            right = self.parse_term()
            left = BinOp(op, left, right)
        return left

    def parse_term(self) -> Any:
        """Level 2: * and / (left-associative)."""
        left = self.parse_pow()
        while self._current().type == 'OP' and self._current().value in ('*', '/'):
            op = self._consume('OP').value
            right = self.parse_pow()
            left = BinOp(op, left, right)
        return left

    def parse_pow(self) -> Any:
        """Level 3: ^ (right-associative)."""
        left = self.parse_primary()
        if self._current().type == 'OP' and self._current().value == '^':
            self._consume('OP')
            right = self.parse_pow()          # right-recursive for right-associativity
            return BinOp('^', left, right)
        return left

    def parse_primary(self) -> Any:
        """Handles atoms: literals, cell refs, ranges, function calls, parentheses, unary -."""
        tok = self._current()

        # Unary minus
        if tok.type == 'OP' and tok.value == '-':
            self._consume('OP')
            expr = self.parse_primary()
            return UnaryMinus(expr)

        # Unary plus (ignore)
        if tok.type == 'OP' and tok.value == '+':
            self._consume('OP')
            return self.parse_primary()

        # Parenthesised expression
        if tok.type == 'OP' and tok.value == '(':
            self._consume('OP', '(')
            expr = self.parse_expr()
            self._consume('OP', ')')
            return expr

        # Number literal
        if tok.type == 'NUMBER':
            self._consume('NUMBER')
            return Literal(float(tok.value))

        # String literal
        if tok.type == 'STRING':
            self._consume('STRING')
            # Strip surrounding double quotes
            return StrLiteral(tok.value[1:-1])

        # Range token (A1:B3) — produced directly by lexer
        if tok.type == 'RANGE':
            self._consume('RANGE')
            start, end = tok.value.split(':')
            return Range(start, end)

        # IDENT — could be function call or cell reference
        if tok.type == 'IDENT':
            name = self._consume('IDENT').value
            # Is it a function call?
            if self._current().type == 'OP' and self._current().value == '(':
                return self._parse_function_call(name)
            # Otherwise it's a cell reference
            return CellRef(name)

        raise SyntaxError(f"Unexpected token: {tok!r}")

    def _parse_function_call(self, name: str) -> Any:
        """Parse a function call after the IDENT token has been consumed."""
        self._consume('OP', '(')

        if name.upper() == 'IF':
            return self._parse_if()

        # Regular function: SUM, AVG, MIN, MAX, or anything else
        args = []
        # Handle empty argument list
        if self._current().type == 'OP' and self._current().value == ')':
            self._consume('OP', ')')
            return FuncCall(name.upper(), args)

        args.append(self._parse_func_arg())
        while self._current().type == 'OP' and self._current().value == ',':
            self._consume('OP', ',')
            args.append(self._parse_func_arg())

        self._consume('OP', ')')
        return FuncCall(name.upper(), args)

    def _parse_func_arg(self) -> Any:
        """
        Parse a single function argument.
        A RANGE token is handled at the lexer level so parse_primary picks it up.
        Otherwise treat as a general expression.
        """
        return self.parse_expr()

    def _parse_if(self) -> IfExpr:
        """
        Parse IF(condition, true_branch, false_branch).
        The condition is: expr comparison_op expr
        """
        lhs = self.parse_expr()

        # Read comparison operator
        tok = self._current()
        if tok.type != 'OP' or tok.value not in ('=', '<>', '<', '<=', '>', '>='):
            raise SyntaxError(f"Expected comparison operator in IF condition, got {tok!r}")
        cond_op = self._consume('OP').value

        rhs = self.parse_expr()

        self._consume('OP', ',')
        true_branch = self.parse_expr()

        self._consume('OP', ',')
        false_branch = self.parse_expr()

        self._consume('OP', ')')

        return IfExpr(cond_op, lhs, rhs, true_branch, false_branch)


def parse(formula: str) -> Any:
    """
    Parse a formula string (with or without leading '=') and return the AST root.
    """
    tokens = tokenize(formula)
    parser = Parser(tokens)
    ast = parser.parse_expr()
    # Ensure all tokens consumed (except EOF)
    if parser._current().type != 'EOF':
        raise SyntaxError(
            f"Unexpected token after expression: {parser._current()!r}"
        )
    return ast
