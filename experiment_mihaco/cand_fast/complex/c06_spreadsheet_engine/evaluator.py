"""evaluator.py — Formula tokenizer and recursive-descent evaluator.

Grammar (left-associative, standard precedence):
    expr   = term   (('+' | '-') term)*
    term   = factor (('*' | '/') factor)*
    factor = NUMBER | CELL_REF | '(' expr ')'
"""

import re

# Regex for cell references: one or more uppercase letters followed by digits.
_CELL_REF_RE = re.compile(r'^[A-Z]+[0-9]+$')
# Regex to find all cell references inside an expression string.
_REF_FIND_RE = re.compile(r'[A-Z]+[0-9]+')
# Regex for a numeric literal (integer or decimal).
_NUMBER_RE = re.compile(r'\d+\.?\d*')


def extract_refs(expr: str) -> list:
    """Return all cell references found in expr (e.g. ['A1', 'B2'])."""
    # Strip the leading '=' if present before scanning.
    body = expr.lstrip('=')
    return _REF_FIND_RE.findall(body)


def evaluate(expr: str, cell_values: dict) -> float:
    """Evaluate a formula expression and return the result as a float.

    Parameters
    ----------
    expr        : formula string, optionally starting with '='
    cell_values : mapping from cell address to its current float value;
                  references absent from this dict default to 0.0
    """
    # Strip leading '=' and surrounding whitespace.
    s = expr.lstrip('=').strip()
    pos = [0]  # mutable position pointer

    def skip_ws() -> None:
        while pos[0] < len(s) and s[pos[0]] == ' ':
            pos[0] += 1

    def parse_expr() -> float:
        """expr = term (('+' | '-') term)*"""
        result = parse_term()
        while True:
            skip_ws()
            if pos[0] < len(s) and s[pos[0]] in ('+', '-'):
                op = s[pos[0]]
                pos[0] += 1
                right = parse_term()
                if op == '+':
                    result += right
                else:
                    result -= right
            else:
                break
        return result

    def parse_term() -> float:
        """term = factor (('*' | '/') factor)*"""
        result = parse_factor()
        while True:
            skip_ws()
            if pos[0] < len(s) and s[pos[0]] in ('*', '/'):
                op = s[pos[0]]
                pos[0] += 1
                right = parse_factor()
                if op == '*':
                    result *= right
                else:
                    # Let ZeroDivisionError propagate naturally.
                    result /= right
            else:
                break
        return result

    def parse_factor() -> float:
        """factor = NUMBER | CELL_REF | '(' expr ')'"""
        skip_ws()
        if pos[0] >= len(s):
            raise ValueError(f"Unexpected end of expression: {expr!r}")

        ch = s[pos[0]]

        # Parenthesised sub-expression.
        if ch == '(':
            pos[0] += 1  # consume '('
            result = parse_expr()
            skip_ws()
            if pos[0] >= len(s) or s[pos[0]] != ')':
                raise ValueError(f"Expected ')' in expression: {expr!r}")
            pos[0] += 1  # consume ')'
            return result

        # Unary minus / plus (e.g. =-A1 or =-3).
        if ch in ('+', '-'):
            sign = 1.0 if ch == '+' else -1.0
            pos[0] += 1
            return sign * parse_factor()

        # Cell reference: starts with an uppercase letter.
        if ch.isupper():
            # Grab the full token ([A-Z]+[0-9]+).
            m = re.match(r'[A-Z]+[0-9]+', s[pos[0]:])
            if m:
                token = m.group(0)
                pos[0] += len(token)
                return float(cell_values.get(token, 0.0))
            raise ValueError(f"Invalid cell reference at pos {pos[0]} in {expr!r}")

        # Numeric literal.
        m = _NUMBER_RE.match(s, pos[0])
        if m:
            pos[0] = m.end()
            return float(m.group(0))

        raise ValueError(f"Unexpected character {ch!r} at pos {pos[0]} in {expr!r}")

    result = parse_expr()
    skip_ws()
    if pos[0] != len(s):
        raise ValueError(f"Unexpected trailing characters in expression: {expr!r}")
    return result
