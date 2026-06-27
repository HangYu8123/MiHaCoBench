"""
parser.py — Recursive-descent / Pratt parser that builds an AST.
"""

from lexer import TType, Token, tokenize


# ---------------------------------------------------------------------------
# AST node types
# ---------------------------------------------------------------------------

class NumLiteral:
    __slots__ = ("value",)
    def __init__(self, value: float):
        self.value = value

class StrLiteral:
    __slots__ = ("value",)
    def __init__(self, value: str):
        self.value = value

class CellRef:
    __slots__ = ("ref",)
    def __init__(self, ref: str):
        self.ref = ref

class RangeRef:
    __slots__ = ("range_str",)
    def __init__(self, range_str: str):
        self.range_str = range_str

class BinOp:
    __slots__ = ("op", "left", "right")
    def __init__(self, op: str, left, right):
        self.op = op
        self.left = left
        self.right = right

class UnaryMinus:
    __slots__ = ("operand",)
    def __init__(self, operand):
        self.operand = operand

class FuncCall:
    __slots__ = ("name", "args")
    def __init__(self, name: str, args: list):
        self.name = name
        self.args = args

class IfExpr:
    __slots__ = ("cmp_op", "left", "right", "true_val", "false_val")
    def __init__(self, cmp_op: str, left, right, true_val, false_val):
        self.cmp_op = cmp_op
        self.left = left
        self.right = right
        self.true_val = true_val
        self.false_val = false_val


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_CMP_TYPES = {TType.EQ, TType.NEQ, TType.LT, TType.LE, TType.GT, TType.GE}
_CMP_STR   = {TType.EQ: '=', TType.NEQ: '<>', TType.LT: '<',
              TType.LE: '<=', TType.GT: '>', TType.GE: '>='}


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self, expected: TType = None) -> Token:
        tok = self._tokens[self._pos]
        if expected is not None and tok.type != expected:
            raise SyntaxError(
                f"Expected {expected} but got {tok.type} ({tok.value!r})"
            )
        self._pos += 1
        return tok

    # ---- expression hierarchy ----

    def parse(self):
        node = self._parse_expr()
        self._consume(TType.EOF)
        return node

    # additive: +  -  (precedence 1, left-assoc)
    def _parse_expr(self):
        left = self._parse_term()
        while self._peek().type in (TType.PLUS, TType.MINUS):
            op = self._consume().value
            right = self._parse_term()
            left = BinOp(op, left, right)
        return left

    # multiplicative: * /  (precedence 2, left-assoc)
    def _parse_term(self):
        left = self._parse_power()
        while self._peek().type in (TType.STAR, TType.SLASH):
            op = self._consume().value
            right = self._parse_power()
            left = BinOp(op, left, right)
        return left

    # exponentiation: ^  (precedence 3, right-assoc)
    def _parse_power(self):
        base = self._parse_unary()
        if self._peek().type == TType.CARET:
            self._consume(TType.CARET)
            exp = self._parse_power()   # right-recursive for right-assoc
            return BinOp('^', base, exp)
        return base

    # unary minus
    def _parse_unary(self):
        if self._peek().type == TType.MINUS:
            self._consume(TType.MINUS)
            operand = self._parse_primary()
            return UnaryMinus(operand)
        return self._parse_primary()

    # primary: literal, ref, func call, parenthesised expr
    def _parse_primary(self):
        tok = self._peek()

        if tok.type == TType.NUMBER:
            self._consume()
            return NumLiteral(tok.value)

        if tok.type == TType.STRING:
            self._consume()
            return StrLiteral(tok.value)

        if tok.type == TType.REF:
            self._consume()
            return CellRef(tok.value)

        if tok.type == TType.RANGE:
            self._consume()
            return RangeRef(tok.value)

        if tok.type == TType.FUNC:
            return self._parse_func()

        if tok.type == TType.LPAREN:
            self._consume(TType.LPAREN)
            node = self._parse_expr()
            self._consume(TType.RPAREN)
            return node

        raise SyntaxError(f"Unexpected token {tok.type} ({tok.value!r})")

    def _parse_func(self):
        name_tok = self._consume(TType.FUNC)
        name = name_tok.value
        self._consume(TType.LPAREN)

        if name == "IF":
            return self._parse_if()

        # SUM / AVG / MIN / MAX: single range OR comma-separated args
        args = []
        # first arg
        args.append(self._parse_func_arg())
        while self._peek().type == TType.COMMA:
            self._consume(TType.COMMA)
            args.append(self._parse_func_arg())
        self._consume(TType.RPAREN)
        return FuncCall(name, args)

    def _parse_func_arg(self):
        """A function argument: range, cell ref, or numeric expression."""
        tok = self._peek()
        if tok.type == TType.RANGE:
            self._consume()
            return RangeRef(tok.value)
        return self._parse_expr()

    def _parse_if(self):
        """
        IF(condition, value_if_true, value_if_false)
        condition: expr cmp_op expr
        """
        left = self._parse_expr()
        cmp_tok = self._peek()
        if cmp_tok.type not in _CMP_TYPES:
            raise SyntaxError(f"Expected comparison operator, got {cmp_tok.type}")
        self._consume()
        cmp_op = _CMP_STR[cmp_tok.type]
        right = self._parse_expr()
        self._consume(TType.COMMA)
        true_val = self._parse_if_branch()
        self._consume(TType.COMMA)
        false_val = self._parse_if_branch()
        self._consume(TType.RPAREN)
        return IfExpr(cmp_op, left, right, true_val, false_val)

    def _parse_if_branch(self):
        """Branch can be a string literal, cell ref, or numeric expression."""
        tok = self._peek()
        if tok.type == TType.STRING:
            self._consume()
            return StrLiteral(tok.value)
        return self._parse_expr()


def parse_formula(formula_body: str):
    """
    Parse a formula body (the part after '=').
    Returns the root AST node.
    """
    tokens = tokenize(formula_body)
    return Parser(tokens).parse()
