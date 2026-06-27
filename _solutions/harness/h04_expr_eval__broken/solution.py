"""BROKEN reference for harness/h04_expr_eval.

PLANTED DEFECT (localized): the ``**`` operator is parsed **left-associative**
instead of right-associative. ``_power`` greedily folds a chain of
``atom ** factor ** factor ...`` from the LEFT, so

    evaluate("2 ** 3 ** 2") == ((2 ** 3) ** 2) == 64.0    # gold: 2 ** (3 ** 2) == 512.0

Everything else is identical to the gold:
  * binary ``+ - * /`` precedence and left-associativity,
  * ``/`` is true division, parentheses, unary chains, decimals,
  * unary minus is still LOOSER than ``**`` (so ``-2 ** 2 == -4.0`` stays correct),
  * a unary sign is still allowed as the exponent's operand (``2 ** -2 == 0.25``),
  * the ``ValueError`` / ``ZeroDivisionError`` exception contract.

So the simple ``+ - * /`` / parenthesis / exception tests all pass on this
variant; only the right-associativity tests (``2**3**2 == 512``,
``2**2**3 == 256``) catch the bug.
"""
from __future__ import annotations

_OPERATORS = {"+", "-", "*", "/", "**", "(", ")"}


def _tokenize(expr: str) -> list[str]:
    """Split ``expr`` into operator and numeric-literal tokens (see gold)."""
    tokens: list[str] = []
    i, n = 0, len(expr)
    while i < n:
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c == "*" and i + 1 < n and expr[i + 1] == "*":
            tokens.append("**")
            i += 2
            continue
        if c in "+-*/()":
            tokens.append(c)
            i += 1
            continue
        if c.isdigit() or c == ".":
            j = i
            dot_seen = False
            while j < n and (expr[j].isdigit() or expr[j] == "."):
                if expr[j] == ".":
                    if dot_seen:
                        raise ValueError(f"malformed numeric literal near index {i}")
                    dot_seen = True
                j += 1
            literal = expr[i:j]
            if literal in (".",):
                raise ValueError("'.' is not a valid numeric literal")
            tokens.append(literal)
            i = j
            continue
        raise ValueError(f"unexpected character {c!r} at index {i}")
    return tokens


class _Parser:
    """Recursive-descent parser/evaluator (BROKEN: left-associative ``**``)."""

    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> str | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expr(self) -> float:
        value = self._term()
        while self._peek() in ("+", "-"):
            op = self._advance()
            rhs = self._term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def _term(self) -> float:
        value = self._factor()
        while self._peek() in ("*", "/"):
            op = self._advance()
            rhs = self._factor()
            if op == "*":
                value = value * rhs
            else:
                if rhs == 0:
                    raise ZeroDivisionError("division by zero")
                value = value / rhs
        return value

    def _factor(self) -> float:
        tok = self._peek()
        if tok == "+":
            self._advance()
            return self._factor()
        if tok == "-":
            self._advance()
            return -self._factor()
        return self._power()

    def _unary_atom(self) -> float:
        """A possibly-signed atom that does NOT consume a following ``**``.

        Used as the exponent operand by the (buggy) left-associative ``_power``
        so that a chain like ``3 ** 2`` is not pre-folded right-associatively
        inside the exponent. Unary signs are still accepted here, so
        ``2 ** -2 == 0.25`` stays correct.
        """
        tok = self._peek()
        if tok == "+":
            self._advance()
            return self._unary_atom()
        if tok == "-":
            self._advance()
            return -self._unary_atom()
        return self._atom()

    def _power(self) -> float:
        base = self._atom()
        # BUG: a *loop* folds the power chain from the LEFT, making ** wrongly
        # left-associative (2 ** 3 ** 2 -> (2 ** 3) ** 2 == 64 instead of 512).
        # The exponent is a *unary atom* (it does not re-enter the ** rule), so
        # the chain is associated left-to-right by this loop. The correct rule
        # recurses on the right operand into a factor instead of looping.
        while self._peek() == "**":
            self._advance()
            exponent = self._unary_atom()
            if base == 0 and exponent < 0:
                raise ZeroDivisionError("0.0 cannot be raised to a negative power")
            base = float(base) ** float(exponent)
        return base

    def _atom(self) -> float:
        tok = self._peek()
        if tok is None:
            raise ValueError("unexpected end of expression (missing operand)")
        if tok == "(":
            self._advance()
            value = self._expr()
            if self._peek() != ")":
                raise ValueError("unbalanced parentheses: missing ')'")
            self._advance()
            return value
        if tok in _OPERATORS:
            raise ValueError(f"unexpected operator {tok!r}; an operand was expected")
        self._advance()  # consume the numeric-literal token
        return float(tok)

    def parse(self) -> float:
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._pos != len(self._tokens):
            raise ValueError(f"unexpected trailing token {self._tokens[self._pos]!r}")
        return value


def evaluate(expr: str) -> float:
    """Evaluate ``expr`` and return a ``float`` (see TASK.md for the contract)."""
    tokens = _tokenize(expr)
    return _Parser(tokens).parse()
