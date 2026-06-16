"""
parser.py — Recursive-descent / Pratt parser that builds an AST.

AST node types (all plain dicts with a 'type' key):
  {'type': 'number', 'value': float}
  {'type': 'string', 'value': str}
  {'type': 'cell_ref', 'ref': str}
  {'type': 'range', 'ref': str}          # only used inside function args
  {'type': 'binop', 'op': str, 'left': node, 'right': node}
  {'type': 'func', 'name': str, 'args': [node]}
  {'type': 'if', 'cond': cond_node, 'then': node, 'else': node}
  {'type': 'cond', 'op': str, 'left': node, 'right': node}
"""

from lexer import Token, TokenType, tokenize
from typing import List


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, ttype: TokenType) -> Token:
        tok = self._advance()
        if tok.type != ttype:
            raise ParseError(f"Expected {ttype}, got {tok.type} ({tok.value!r})")
        return tok

    def parse(self):
        """Parse and return the root AST node."""
        node = self._parse_expr()
        self._expect(TokenType.EOF)
        return node

    # ---------- Pratt / precedence-climbing ----------

    def _parse_expr(self):
        return self._parse_additive()

    def _parse_additive(self):
        left = self._parse_multiplicative()
        while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def _parse_multiplicative(self):
        left = self._parse_power()
        while self._peek().type in (TokenType.STAR, TokenType.SLASH):
            op = self._advance().value
            right = self._parse_power()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def _parse_power(self):
        """Right-associative: 2^3^2 == 2^(3^2) == 512"""
        base = self._parse_unary()
        if self._peek().type == TokenType.CARET:
            self._advance()
            exp = self._parse_power()  # right-recursive for right-assoc
            return {'type': 'binop', 'op': '^', 'left': base, 'right': exp}
        return base

    def _parse_unary(self):
        if self._peek().type == TokenType.MINUS:
            self._advance()
            operand = self._parse_primary()
            return {'type': 'binop', 'op': '*',
                    'left': {'type': 'number', 'value': -1.0},
                    'right': operand}
        return self._parse_primary()

    def _parse_primary(self):
        tok = self._peek()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return {'type': 'number', 'value': tok.value}

        if tok.type == TokenType.STRING:
            self._advance()
            return {'type': 'string', 'value': tok.value}

        if tok.type == TokenType.CELL_REF:
            self._advance()
            return {'type': 'cell_ref', 'ref': tok.value}

        if tok.type == TokenType.RANGE:
            self._advance()
            return {'type': 'range', 'ref': tok.value}

        if tok.type == TokenType.FUNC:
            return self._parse_func_call()

        if tok.type == TokenType.LPAREN:
            self._advance()
            node = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return node

        raise ParseError(f"Unexpected token {tok.type} ({tok.value!r})")

    def _parse_func_call(self):
        name_tok = self._advance()  # FUNC token
        name = name_tok.value
        self._expect(TokenType.LPAREN)

        if name == 'IF':
            return self._parse_if()

        # SUM, AVG, MIN, MAX — one range arg or comma-separated refs/literals
        args = self._parse_func_args()
        self._expect(TokenType.RPAREN)
        return {'type': 'func', 'name': name, 'args': args}

    def _parse_if(self):
        """IF(condition, true_expr, false_expr)"""
        cond = self._parse_condition()
        self._expect(TokenType.COMMA)
        then_expr = self._parse_expr()
        self._expect(TokenType.COMMA)
        else_expr = self._parse_expr()
        self._expect(TokenType.RPAREN)
        return {'type': 'if', 'cond': cond, 'then': then_expr, 'else': else_expr}

    def _parse_condition(self):
        """Parse: expr comparator expr"""
        left = self._parse_expr()
        cmp_types = (TokenType.EQ, TokenType.NEQ, TokenType.LT,
                     TokenType.LTE, TokenType.GT, TokenType.GTE)
        tok = self._peek()
        if tok.type not in cmp_types:
            raise ParseError(f"Expected comparison operator, got {tok.type}")
        op = self._advance().value
        right = self._parse_expr()
        return {'type': 'cond', 'op': op, 'left': left, 'right': right}

    def _parse_func_args(self):
        """Parse comma-separated arguments (for SUM/AVG/MIN/MAX)."""
        args = []
        if self._peek().type == TokenType.RPAREN:
            return args  # empty arg list
        args.append(self._parse_func_arg())
        while self._peek().type == TokenType.COMMA:
            self._advance()
            args.append(self._parse_func_arg())
        return args

    def _parse_func_arg(self):
        """A function argument can be a range, cell ref, or expression."""
        tok = self._peek()
        if tok.type == TokenType.RANGE:
            self._advance()
            return {'type': 'range', 'ref': tok.value}
        return self._parse_expr()


def parse_formula(formula: str):
    """
    Parse a formula string (WITHOUT the leading '=').
    Returns the root AST node.
    """
    tokens = tokenize(formula)
    parser = Parser(tokens)
    return parser.parse()
