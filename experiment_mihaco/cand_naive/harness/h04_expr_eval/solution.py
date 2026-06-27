"""expr_eval: Arithmetic expression evaluator with precise precedence."""


class _Tok:
    NUM = "NUM"
    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    DIV = "/"
    POW = "**"
    LPAREN = "("
    RPAREN = ")"


def _tokenize(expr):
    """Turn ``expr`` into a list of (type, value) tokens."""
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        c = expr[i]

        if c.isspace():
            i += 1
            continue

        if c.isdigit() or c == ".":
            start = i
            dot_count = 0
            digit_count = 0
            while i < n and (expr[i].isdigit() or expr[i] == "."):
                if expr[i] == ".":
                    dot_count += 1
                else:
                    digit_count += 1
                i += 1
            literal = expr[start:i]
            if dot_count > 1 or digit_count == 0:
                raise ValueError("malformed numeric literal: %r" % literal)
            tokens.append((_Tok.NUM, float(literal)))
            continue

        if c == "*":
            if i + 1 < n and expr[i + 1] == "*":
                tokens.append((_Tok.POW, "**"))
                i += 2
            else:
                tokens.append((_Tok.MUL, "*"))
                i += 1
            continue

        if c == "+":
            tokens.append((_Tok.PLUS, "+"))
            i += 1
            continue
        if c == "-":
            tokens.append((_Tok.MINUS, "-"))
            i += 1
            continue
        if c == "/":
            tokens.append((_Tok.DIV, "/"))
            i += 1
            continue
        if c == "(":
            tokens.append((_Tok.LPAREN, "("))
            i += 1
            continue
        if c == ")":
            tokens.append((_Tok.RPAREN, ")"))
            i += 1
            continue

        raise ValueError("unknown character: %r" % c)

    return tokens


class _Parser:
    """Recursive-descent parser/evaluator over the token list."""

    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return (None, None)

    def _advance(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse(self):
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._pos != len(self._tokens):
            raise ValueError("unexpected trailing tokens")
        return value

    def _expr(self):
        value = self._term()
        while True:
            ttype, _ = self._peek()
            if ttype == _Tok.PLUS:
                self._advance()
                value = value + self._term()
            elif ttype == _Tok.MINUS:
                self._advance()
                value = value - self._term()
            else:
                break
        return value

    def _term(self):
        value = self._unary()
        while True:
            ttype, _ = self._peek()
            if ttype == _Tok.MUL:
                self._advance()
                value = value * self._unary()
            elif ttype == _Tok.DIV:
                self._advance()
                divisor = self._unary()
                if divisor == 0:
                    raise ZeroDivisionError("division by zero")
                value = value / divisor
            else:
                break
        return value

    def _unary(self):
        ttype, _ = self._peek()
        if ttype == _Tok.PLUS:
            self._advance()
            return +self._unary()
        if ttype == _Tok.MINUS:
            self._advance()
            return -self._unary()
        return self._power()

    def _power(self):
        base = self._atom()
        ttype, _ = self._peek()
        if ttype == _Tok.POW:
            self._advance()
            exponent = self._unary()
            if base == 0 and exponent < 0:
                raise ZeroDivisionError("0 raised to a negative power")
            return float(base ** exponent)
        return base

    def _atom(self):
        ttype, value = self._peek()
        if ttype == _Tok.NUM:
            self._advance()
            return float(value)
        if ttype == _Tok.LPAREN:
            self._advance()
            inner = self._expr()
            ttype2, _ = self._peek()
            if ttype2 != _Tok.RPAREN:
                raise ValueError("expected ')'")
            self._advance()
            return inner
        if ttype is None:
            raise ValueError("unexpected end of expression; operand expected")
        raise ValueError("unexpected token where operand expected: %r" % (value,))


def evaluate(expr: str) -> float:
    """Evaluate ``expr`` and return the result as a ``float``."""
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    tokens = _tokenize(expr)
    result = _Parser(tokens).parse()
    return float(result)
