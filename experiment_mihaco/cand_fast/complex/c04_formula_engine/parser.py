"""
parser.py — Recursive-descent / Pratt parser that builds an AST.

AST node types:
  NumberNode(value: float)
  StringNode(value: str)
  CellRefNode(ref: str)
  RangeNode(ref: str)
  BinOpNode(op: str, left, right)
  UnaryMinusNode(operand)
  FuncCallNode(name: str, args: list)
  IfNode(cond_op: str, lhs, rhs, true_val, false_val)
"""

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# AST node definitions
# ---------------------------------------------------------------------------

@dataclass
class NumberNode:
    value: float


@dataclass
class StringNode:
    value: str


@dataclass
class CellRefNode:
    ref: str


@dataclass
class RangeNode:
    ref: str


@dataclass
class BinOpNode:
    op: str
    left: Any
    right: Any


@dataclass
class UnaryMinusNode:
    operand: Any


@dataclass
class FuncCallNode:
    name: str
    args: list = field(default_factory=list)


@dataclass
class IfNode:
    cond_op: str
    lhs: Any
    rhs: Any
    true_val: Any
    false_val: Any


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_COMPARISON_OPS = {'=', '<>', '<', '<=', '>', '>='}


class Parser:
    def __init__(self, tokens: list):
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, tok_type, tok_val=None):
        tok = self._consume()
        if tok[0] != tok_type:
            raise ValueError(f"Expected {tok_type!r} but got {tok!r}")
        if tok_val is not None and tok[1] != tok_val:
            raise ValueError(f"Expected {tok_val!r} but got {tok[1]!r}")
        return tok

    def _match_op(self, *ops):
        tok = self._peek()
        if tok and tok[0] == 'OP' and tok[1] in ops:
            return self._consume()
        return None

    # ------------------------------------------------------------------
    # Grammar rules (precedence climbing)
    # ------------------------------------------------------------------

    def parse(self):
        node = self._parse_additive()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token after expression: {self._peek()!r}")
        return node

    def _parse_additive(self):
        """Handles + and - (left-associative, precedence 1)."""
        left = self._parse_multiplicative()
        while True:
            tok = self._match_op('+', '-')
            if tok is None:
                break
            right = self._parse_multiplicative()
            left = BinOpNode(tok[1], left, right)
        return left

    def _parse_multiplicative(self):
        """Handles * and / (left-associative, precedence 2)."""
        left = self._parse_power()
        while True:
            tok = self._match_op('*', '/')
            if tok is None:
                break
            right = self._parse_power()
            left = BinOpNode(tok[1], left, right)
        return left

    def _parse_power(self):
        """Handles ^ (right-associative, precedence 3)."""
        base = self._parse_unary()
        tok = self._match_op('^')
        if tok is None:
            return base
        # Right-associative: recurse at the same level
        exponent = self._parse_power()
        return BinOpNode('^', base, exponent)

    def _parse_unary(self):
        """Handles unary minus."""
        tok = self._match_op('-')
        if tok:
            operand = self._parse_primary()
            # Fold unary minus into number literals directly
            if isinstance(operand, NumberNode):
                return NumberNode(-operand.value)
            return UnaryMinusNode(operand)
        return self._parse_primary()

    def _parse_primary(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of formula")

        # Numeric literal
        if tok[0] == 'NUMBER':
            self._consume()
            return NumberNode(tok[1])

        # String literal
        if tok[0] == 'STRING':
            self._consume()
            return StringNode(tok[1])

        # Range (e.g. A1:B3) — only valid inside function calls
        if tok[0] == 'RANGE':
            self._consume()
            return RangeNode(tok[1])

        # Cell reference
        if tok[0] == 'CELL':
            self._consume()
            return CellRefNode(tok[1])

        # Function call: IF, SUM, AVG, MIN, MAX
        if tok[0] == 'FUNC':
            return self._parse_func_call()

        # Parenthesised sub-expression
        if tok[0] == 'OP' and tok[1] == '(':
            self._consume()  # eat '('
            node = self._parse_additive()
            self._expect('OP', ')')
            return node

        raise ValueError(f"Unexpected token: {tok!r}")

    def _parse_func_call(self):
        name_tok = self._consume()   # FUNC token
        name = name_tok[1]
        self._expect('OP', '(')

        if name == 'IF':
            return self._parse_if()

        # SUM / AVG / MIN / MAX: single range OR comma-separated list
        args = self._parse_arg_list()
        self._expect('OP', ')')
        return FuncCallNode(name, args)

    def _parse_if(self):
        """IF(lhs OP rhs, true_val, false_val) — already consumed 'IF('."""
        lhs = self._parse_additive()

        # Comparison operator
        tok = self._consume()
        if tok[0] != 'OP' or tok[1] not in _COMPARISON_OPS:
            raise ValueError(f"Expected comparison operator in IF condition, got {tok!r}")
        cond_op = tok[1]

        rhs = self._parse_additive()

        self._expect('OP', ',')
        true_val = self._parse_value_or_expr()
        self._expect('OP', ',')
        false_val = self._parse_value_or_expr()
        self._expect('OP', ')')

        return IfNode(cond_op, lhs, rhs, true_val, false_val)

    def _parse_value_or_expr(self):
        """Parse a branch value: string literal, numeric expression, or cell ref."""
        tok = self._peek()
        if tok and tok[0] == 'STRING':
            self._consume()
            return StringNode(tok[1])
        return self._parse_additive()

    def _parse_arg_list(self):
        """Parse comma-separated arguments for SUM/AVG/MIN/MAX."""
        args = []
        # First argument
        args.append(self._parse_single_arg())
        while self._match_op(','):
            args.append(self._parse_single_arg())
        return args

    def _parse_single_arg(self):
        """One argument: either a RANGE token or a general additive expression."""
        tok = self._peek()
        if tok and tok[0] == 'RANGE':
            self._consume()
            return RangeNode(tok[1])
        return self._parse_additive()


def parse(tokens: list):
    """Parse a token list and return the root AST node."""
    return Parser(tokens).parse()
