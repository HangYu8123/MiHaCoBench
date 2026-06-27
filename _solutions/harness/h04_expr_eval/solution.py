"""Gold reference for harness/h04_expr_eval.

A recursive-descent evaluator for arithmetic expressions over the reals.

The whole difficulty is the **precedence/associativity lattice**, which is
encoded directly in the grammar (lowest precedence binds loosest, parsed
outermost):

    expr   := term   (('+' | '-') term)*        # binary +/-, left-assoc
    term   := factor (('*' | '/') factor)*       # binary *,/  left-assoc (/ is true division)
    factor := ('+' | '-') factor | power         # unary +/-, LOOSER than **
    power  := atom ('**' factor)?                # **, RIGHT-assoc; exponent is `factor`
    atom   := NUMBER | '(' expr ')'

Two consequences fall out of putting unary above ``power`` (so unary is looser
than ``**``) while making ``power``'s right operand a *factor* (so it is
right-associative AND may itself begin with a unary sign):

  * ``-2 ** 2`` parses as ``factor -> -(power)`` = ``-(2 ** 2)`` = ``-4``.
  * ``2 ** 3 ** 2`` parses as ``2 ** (3 ** 2)`` = ``512`` (right-associative,
    because the exponent rule recurses into ``factor`` which descends back into
    ``power``).
  * ``2 ** -2`` is legal: the exponent ``factor`` may start with unary ``-``.

Every result is a Python ``float`` (``/`` is true division, ``**`` is
``float`` because at least one operand is coerced to float). Malformed input
raises ``ValueError``; division by zero and ``0 ** negative`` raise
``ZeroDivisionError``.
"""
from __future__ import annotations

# Token kinds emitted by the lexer.
_OPERATORS = {"+", "-", "*", "/", "**", "(", ")"}


def _tokenize(expr: str) -> list[str]:
    """Split ``expr`` into a list of operator and numeric-literal tokens.

    Whitespace is insignificant. Numeric literals are non-negative integer or
    decimal literals (``12``, ``3.5``, ``.5``, ``2.``). ``**`` is recognised as a
    single token (greedily, before ``*``).

    Raises
    ------
    ValueError
        On any character that cannot begin a valid token, or a malformed numeric
        literal (e.g. more than one ``.``).
    """
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
                    if dot_seen:  # a second '.' in one literal -> malformed
                        raise ValueError(f"malformed numeric literal near index {i}")
                    dot_seen = True
                j += 1
            literal = expr[i:j]
            if literal in (".",):  # a lone '.' is not a number
                raise ValueError("'.' is not a valid numeric literal")
            tokens.append(literal)
            i = j
            continue
        raise ValueError(f"unexpected character {c!r} at index {i}")
    return tokens


class _Parser:
    """Recursive-descent parser/evaluator over a token list.

    The grammar (and therefore the precedence/associativity) is encoded in the
    mutual recursion of :meth:`_expr`, :meth:`_term`, :meth:`_factor`,
    :meth:`_power`, :meth:`_atom`.
    """

    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> str | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    # expr := term (('+' | '-') term)*      [binary +/-, left-associative]
    def _expr(self) -> float:
        value = self._term()
        while self._peek() in ("+", "-"):
            op = self._advance()
            rhs = self._term()
            value = value + rhs if op == "+" else value - rhs
        return value

    # term := factor (('*' | '/') factor)*  [binary *,/, left-associative]
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
                value = value / rhs  # true division -> always float
        return value

    # factor := ('+' | '-') factor | power  [unary +/-, LOOSER than **]
    def _factor(self) -> float:
        tok = self._peek()
        if tok == "+":
            self._advance()
            return self._factor()
        if tok == "-":
            self._advance()
            return -self._factor()
        return self._power()

    # power := atom ('**' factor)?          [**, RIGHT-associative; exponent is a factor]
    def _power(self) -> float:
        base = self._atom()
        if self._peek() == "**":
            self._advance()
            # Recurse into _factor (not _power): this makes ** right-associative
            # AND lets the exponent begin with a unary sign (e.g. 2 ** -2).
            exponent = self._factor()
            if base == 0 and exponent < 0:
                raise ZeroDivisionError("0.0 cannot be raised to a negative power")
            return float(base) ** float(exponent)
        return base

    # atom := NUMBER | '(' expr ')'
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
            # An operator where an operand was expected (e.g. leading '*', '**',
            # or two adjacent binary operators).
            raise ValueError(f"unexpected operator {tok!r}; an operand was expected")
        self._advance()  # consume the numeric-literal token
        return float(tok)  # numeric literal; always returns a float

    def parse(self) -> float:
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._pos != len(self._tokens):
            # Leftover tokens: e.g. "1 2" (juxtaposed literals) or a stray ')'.
            raise ValueError(f"unexpected trailing token {self._tokens[self._pos]!r}")
        return value


def evaluate(expr: str) -> float:
    """Evaluate the arithmetic expression ``expr`` and return a ``float``.

    Grammar tokens: non-negative integer/decimal literals, the binary operators
    ``+ - * /`` and ``**``, unary ``+``/``-``, and parentheses. Whitespace is
    insignificant.

    Precedence, lowest (binds loosest) to highest (binds tightest):

      1. binary ``+`` ``-``   (left-associative)
      2. binary ``*`` ``/``   (left-associative; ``/`` is true division)
      3. unary ``+`` ``-``
      4. ``**``               (right-associative, binds tighter than unary minus)

    Returns
    -------
    float
        The value of the expression (always a ``float``).

    Raises
    ------
    ZeroDivisionError
        On division by zero, or ``0`` raised to a negative power.
    ValueError
        On any malformed expression: empty/blank input, unbalanced parentheses, a
        missing/trailing operand, two adjacent binary operators, or an unknown
        character.
    """
    tokens = _tokenize(expr)
    return _Parser(tokens).parse()
