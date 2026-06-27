"""
evaluator.py — Formula tokenizer and evaluator for the mini spreadsheet engine.

Supported grammar (recursive descent parser):
    expr   := term (('+' | '-') term)*
    term   := factor (('*' | '/') factor)*
    factor := NUMBER | CELLREF | '(' expr ')' | ('+' | '-') factor
"""

import re


# Regex patterns for tokenization
_TOKEN_RE = re.compile(
    r"""
    (?P<NUMBER>   \d+(?:\.\d+)? )   |   # integer or float literal
    (?P<CELLREF>  [A-Z]+\d+     )   |   # cell reference like A1, B12, AA10
    (?P<PLUS>     \+            )   |
    (?P<MINUS>    -             )   |
    (?P<STAR>     \*            )   |
    (?P<SLASH>    /             )   |
    (?P<LPAREN>   \(            )   |
    (?P<RPAREN>   \)            )   |
    (?P<SPACE>    \s+           )       # whitespace (ignored)
    """,
    re.VERBOSE,
)


def tokenize(expr: str) -> list[tuple[str, str]]:
    """
    Tokenize a formula string (with leading '=' already stripped).
    Returns a list of (type, value) tuples, skipping whitespace.
    """
    tokens = []
    for m in _TOKEN_RE.finditer(expr):
        kind = m.lastgroup
        if kind == "SPACE":
            continue
        tokens.append((kind, m.group()))
    return tokens


def extract_cell_refs(expr: str) -> list[str]:
    """
    Return all cell references found in the formula string
    (with leading '=' already stripped).
    """
    return re.findall(r'[A-Z]+\d+', expr)


class Parser:
    """
    Recursive descent parser that evaluates an arithmetic expression.
    Cell values are provided via a lookup callable.
    """

    def __init__(self, tokens: list[tuple[str, str]], cell_lookup):
        self._tokens = tokens
        self._pos = 0
        self._lookup = cell_lookup

    def _peek(self) -> tuple[str, str] | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self) -> tuple[str, str]:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse_expr(self) -> float:
        """expr := term (('+' | '-') term)*"""
        result = self.parse_term()
        while True:
            tok = self._peek()
            if tok is None:
                break
            kind, val = tok
            if kind == "PLUS":
                self._consume()
                result += self.parse_term()
            elif kind == "MINUS":
                self._consume()
                result -= self.parse_term()
            else:
                break
        return result

    def parse_term(self) -> float:
        """term := factor (('*' | '/') factor)*"""
        result = self.parse_factor()
        while True:
            tok = self._peek()
            if tok is None:
                break
            kind, val = tok
            if kind == "STAR":
                self._consume()
                result *= self.parse_factor()
            elif kind == "SLASH":
                self._consume()
                divisor = self.parse_factor()
                if divisor == 0.0:
                    raise ZeroDivisionError("Division by zero in formula.")
                result /= divisor
            else:
                break
        return result

    def parse_factor(self) -> float:
        """factor := NUMBER | CELLREF | '(' expr ')' | ('+' | '-') factor"""
        tok = self._peek()
        if tok is None:
            raise SyntaxError("Unexpected end of expression.")

        kind, val = tok

        if kind == "NUMBER":
            self._consume()
            return float(val)

        if kind == "CELLREF":
            self._consume()
            return float(self._lookup(val))

        if kind == "LPAREN":
            self._consume()  # consume '('
            result = self.parse_expr()
            closing = self._peek()
            if closing is None or closing[0] != "RPAREN":
                raise SyntaxError("Missing closing parenthesis.")
            self._consume()  # consume ')'
            return result

        if kind == "PLUS":
            self._consume()
            return +self.parse_factor()

        if kind == "MINUS":
            self._consume()
            return -self.parse_factor()

        raise SyntaxError(f"Unexpected token: {val!r}")


def evaluate_formula(expr: str, cell_lookup) -> float:
    """
    Evaluate a formula string.
    `expr` must start with '='.
    `cell_lookup(cell_name)` returns the numeric value of a cell.
    """
    if not expr.startswith("="):
        raise ValueError(f"Formula must start with '=': {expr!r}")
    body = expr[1:]
    tokens = tokenize(body)
    parser = Parser(tokens, cell_lookup)
    result = parser.parse_expr()
    # Make sure we consumed all tokens
    if parser._peek() is not None:
        raise SyntaxError(f"Unexpected token after expression: {parser._peek()}")
    return float(result)
