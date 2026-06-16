"""
parser.py — Pratt/precedence-climbing recursive-descent parser.

Builds an AST from a token list produced by lexer.tokenize().

AST node types (dataclasses):
  NumNode(value: float)
  StrNode(value: str)
  CellNode(ref: str)
  RangeNode(ref: str)             e.g. "A1:B3"
  BinOpNode(op: str, left, right)
  UnaryNode(op: str, operand)
  FuncNode(name: str, args: list)
  IfNode(cond, true_branch, false_branch)

Binding powers:
  CMP ops (<=, >=, <>, <, >, =) : 0  (lowest, lower than arithmetic)
  + -                            : 1
  * /                            : 2
  ^                              : 3  (right-associative)
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from lexer import tokenize, Token


# ─── AST nodes ───────────────────────────────────────────────────────────────

@dataclass
class NumNode:
    value: float


@dataclass
class StrNode:
    value: str


@dataclass
class CellNode:
    ref: str


@dataclass
class RangeNode:
    ref: str  # e.g. "A1:B3"


@dataclass
class BinOpNode:
    op: str
    left: Any
    right: Any


@dataclass
class UnaryNode:
    op: str
    operand: Any


@dataclass
class FuncNode:
    name: str
    args: list = field(default_factory=list)


@dataclass
class IfNode:
    cond: Any
    true_branch: Any
    false_branch: Any


# ─── Binding powers ───────────────────────────────────────────────────────────

_INFIX_BP = {
    '+': 1, '-': 1,
    '*': 2, '/': 2,
    '^': 3,
}

_CMP_OPS = {'<=', '>=', '<>', '<', '>', '='}
_CMP_BP = 0  # lower than any arithmetic


# ─── Parser class ─────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Optional[Token]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self, expected_type: Optional[str] = None) -> Token:
        tok = self._peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        if expected_type is not None and tok.type != expected_type:
            raise SyntaxError(
                f"Expected {expected_type} but got {tok.type}={tok.value!r}"
            )
        self._pos += 1
        return tok

    def parse(self) -> Any:
        node = self.parse_expr(0)
        if self._peek() is not None:
            raise SyntaxError(f"Unexpected token: {self._peek()}")
        return node

    def parse_expr(self, min_bp: int) -> Any:
        left = self.parse_primary()

        while True:
            tok = self._peek()
            if tok is None:
                break

            if tok.type == 'OP':
                op = tok.value
                bp = _INFIX_BP.get(op)
                if bp is None or bp <= min_bp:
                    break
                self._consume('OP')
                # ^ is right-associative: recurse at same bp
                if op == '^':
                    right = self.parse_expr(bp - 1)
                else:
                    right = self.parse_expr(bp)
                left = BinOpNode(op, left, right)

            elif tok.type == 'CMP':
                # CMP ops have bp=0; only entered when min_bp < 0, which never
                # happens in normal parsing, so we handle them at min_bp==0 too.
                if _CMP_BP < min_bp:
                    break
                op = tok.value
                self._consume('CMP')
                right = self.parse_expr(_CMP_BP + 1)
                left = BinOpNode(op, left, right)

            else:
                break

        return left

    def parse_primary(self) -> Any:
        tok = self._peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input in parse_primary")

        # Unary minus (or plus)
        if tok.type == 'OP' and tok.value in ('-', '+'):
            self._consume('OP')
            operand = self.parse_primary()
            if tok.value == '-':
                return UnaryNode('-', operand)
            return operand  # unary + is identity

        if tok.type == 'NUMBER':
            self._consume('NUMBER')
            return NumNode(float(tok.value))

        if tok.type == 'STRING':
            self._consume('STRING')
            # Strip surrounding double quotes
            return StrNode(tok.value[1:-1])

        if tok.type == 'RANGE':
            self._consume('RANGE')
            return RangeNode(tok.value)

        if tok.type == 'FUNC_NAME':
            self._consume('FUNC_NAME')
            return self.parse_call(tok.value)

        if tok.type == 'CELL_REF':
            self._consume('CELL_REF')
            return CellNode(tok.value)

        if tok.type == 'LPAREN':
            self._consume('LPAREN')
            node = self.parse_expr(0)
            self._consume('RPAREN')
            return node

        raise SyntaxError(f"Unexpected token in parse_primary: {tok}")

    def parse_call(self, name: str) -> Any:
        self._consume('LPAREN')

        if name == 'IF':
            cond = self.parse_expr(0)
            self._consume('COMMA')
            true_branch = self.parse_expr(0)
            self._consume('COMMA')
            false_branch = self.parse_expr(0)
            self._consume('RPAREN')
            return IfNode(cond, true_branch, false_branch)

        # SUM, AVG, MIN, MAX — parse comma-separated args
        args = []
        tok = self._peek()
        if tok is not None and tok.type != 'RPAREN':
            args.append(self.parse_expr(0))
            while self._peek() is not None and self._peek().type == 'COMMA':
                self._consume('COMMA')
                args.append(self.parse_expr(0))

        self._consume('RPAREN')
        return FuncNode(name, args)


# ─── Public entry point ───────────────────────────────────────────────────────

def parse_formula(formula: str) -> Any:
    """
    Parse a formula string (without leading '=') and return the AST root.
    """
    tokens = tokenize(formula)
    parser = Parser(tokens)
    return parser.parse()
