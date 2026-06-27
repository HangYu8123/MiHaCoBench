"""
evaluator.py — Formula tokenizer and recursive-descent parser/evaluator.

Supports:
  - Numeric literals (integers and floats)
  - Cell references: one or more uppercase letters followed by one or more digits
  - Arithmetic: +, -, *, /  (with correct precedence: * and / bind tighter)
  - Parentheses for grouping
"""
import re

# Tokenizer pattern: matches floats/ints, cell refs, operators, parentheses.
_TOKEN_RE = re.compile(r'\d+\.?\d*|\.[0-9]+|[A-Z]+[0-9]+|[+\-*/()]')


def extract_cell_refs(expr: str) -> list:
    """
    Return a list of all cell references found in `expr`.

    `expr` may or may not start with '='; the leading '=' is stripped first.
    """
    body = expr.lstrip('=')
    return re.findall(r'[A-Z]+[0-9]+', body)


def evaluate(expr: str, lookup) -> float:
    """
    Evaluate a formula expression and return its value as a float.

    Parameters
    ----------
    expr : str
        A formula string, optionally prefixed with '='.
    lookup : callable
        A function `lookup(cell: str) -> float` that returns the current
        value of a referenced cell.

    Returns
    -------
    float
        The computed value.
    """
    body = expr.lstrip('=')
    tokens = _TOKEN_RE.findall(body)
    pos = [0]  # mutable position pointer

    def peek():
        if pos[0] < len(tokens):
            return tokens[pos[0]]
        return None

    def consume():
        tok = tokens[pos[0]]
        pos[0] += 1
        return tok

    def parse_expr():
        """expr = term (('+' | '-') term)*"""
        result = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            if op == '+':
                result += right
            else:
                result -= right
        return result

    def parse_term():
        """term = factor (('*' | '/') factor)*"""
        result = parse_factor()
        while peek() in ('*', '/'):
            op = consume()
            right = parse_factor()
            if op == '*':
                result *= right
            else:
                result /= right
        return result

    def parse_factor():
        """factor = '(' expr ')' | NUMBER | CELL_REF"""
        tok = peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")

        if tok == '(':
            consume()  # consume '('
            val = parse_expr()
            close = consume()  # consume ')'
            if close != ')':
                raise ValueError(f"Expected ')' but got '{close}'")
            return val

        # Try numeric literal
        try:
            val = float(tok)
            consume()
            return val
        except ValueError:
            pass

        # Must be a cell reference
        if re.match(r'^[A-Z]+[0-9]+$', tok):
            consume()
            return float(lookup(tok))

        raise ValueError(f"Unexpected token: '{tok}'")

    result = parse_expr()
    if pos[0] != len(tokens):
        raise ValueError(f"Unexpected trailing tokens: {tokens[pos[0]:]}")
    return float(result)
