"""Recursive-descent parser for the mini-SQL dialect (gold reference).

Consumes the token list from :mod:`tokenizer` and produces a small AST of
plain dataclasses. The parser is responsible only for **syntax**; all semantic
checks (unknown table/column, type mismatch, GROUP BY validity, NULL logic)
live in :mod:`engine`. A syntactically malformed statement raises
:class:`ValueError`.

Statement AST
-------------
``CreateTable(table, columns)``  columns = list of ``(name, type)`` with type in
                                 ``{"INT", "TEXT"}``
``Insert(table, columns, values)`` columns is ``None`` for positional inserts;
                                   values is a list of literal AST nodes
``Select(distinct, select_list, table, where, group_by, order_by, limit, offset)``

Expression / select AST
------------------------
``Literal(value)``                int / str / None
``Column(name)``                  a bare column reference
``Aggregate(func, arg)``          func in COUNT/SUM/AVG/MIN/MAX; arg is ``"*"``
                                  (COUNT(*) only) or a column name string
``SelectItem(expr, alias, text)`` one select-list entry; ``text`` is the exact
                                  source spelling used as the default result key
``Compare(col, op, literal)``     a column-vs-literal comparison (normalised so
                                  the column is on the left and ``op`` flipped if
                                  the literal was written first)
``IsNull(col, negated)``          ``col IS NULL`` / ``col IS NOT NULL``
``Not(operand)`` / ``And(left,right)`` / ``Or(left,right)``  boolean combinators
``OrderKey(col, descending)``     one ORDER BY key
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tokenizer import (
    Token, tokenize,
    KW, IDENT, INT, STR, NULL, STAR, COMMA, LPAREN, RPAREN, OP, EOF,
)


# --------------------------------------------------------------------------- #
# AST node classes
# --------------------------------------------------------------------------- #
@dataclass
class Literal:
    value: object


@dataclass
class Column:
    name: str


@dataclass
class Aggregate:
    func: str          # COUNT | SUM | AVG | MIN | MAX
    arg: str           # "*" (COUNT only) or a column name


@dataclass
class SelectItem:
    expr: object       # Column | Aggregate
    alias: Optional[str]
    text: str          # exact source spelling (default result key)


@dataclass
class Compare:
    col: str
    op: str            # = <> < <= > >=
    literal: object    # int | str | None


@dataclass
class IsNull:
    col: str
    negated: bool


@dataclass
class Not:
    operand: object


@dataclass
class And:
    left: object
    right: object


@dataclass
class Or:
    left: object
    right: object


@dataclass
class OrderKey:
    col: str
    descending: bool


@dataclass
class CreateTable:
    table: str
    columns: list  # list[(name, type)]


@dataclass
class Insert:
    table: str
    columns: Optional[list]   # None => positional
    values: list              # list[Literal]


@dataclass
class Select:
    distinct: bool
    select_list: list         # list[SelectItem] or the string "*"
    table: str
    where: object             # condition AST or None
    group_by: Optional[list]  # list[str] or None
    order_by: Optional[list]  # list[OrderKey] or None
    limit: Optional[int]
    offset: Optional[int]


# Operators that may appear as comparisons, and their mirror (used when the
# literal is written before the column so we can normalise column-on-left).
_FLIP = {"=": "=", "<>": "<>", "<": ">", "<=": ">=", ">": "<", ">=": "<="}


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.toks = tokens
        self.pos = 0

    # --- token navigation --------------------------------------------------
    def _peek(self) -> Token:
        return self.toks[self.pos]

    def _next(self) -> Token:
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def _at_kw(self, *words: str) -> bool:
        t = self._peek()
        return t.kind == KW and t.value in words

    def _eat_kw(self, word: str) -> None:
        t = self._next()
        if not (t.kind == KW and t.value == word):
            raise ValueError(f"expected keyword {word}, got {t.value!r}")

    def _expect(self, kind: str) -> Token:
        t = self._next()
        if t.kind != kind:
            raise ValueError(f"expected {kind}, got {t.kind} {t.value!r}")
        return t

    def _expect_ident(self) -> str:
        t = self._next()
        if t.kind != IDENT:
            raise ValueError(f"expected identifier, got {t.kind} {t.value!r}")
        return t.value

    # --- top-level dispatch ------------------------------------------------
    def parse_statement(self):
        t = self._peek()
        if t.kind != KW:
            raise ValueError("statement must start with a keyword")
        if t.value == "CREATE":
            node = self._parse_create()
        elif t.value == "INSERT":
            node = self._parse_insert()
        elif t.value == "SELECT":
            node = self._parse_select()
        else:
            raise ValueError(f"unsupported statement {t.value!r}")
        if self._peek().kind != EOF:
            raise ValueError("trailing tokens after statement")
        return node

    # --- CREATE TABLE ------------------------------------------------------
    def _parse_create(self) -> CreateTable:
        self._eat_kw("CREATE")
        self._eat_kw("TABLE")
        table = self._expect_ident()
        self._expect(LPAREN)
        columns: list = []
        while True:
            name = self._expect_ident()
            tt = self._next()
            if not (tt.kind == KW and tt.value in ("INT", "TEXT")):
                raise ValueError("column type must be INT or TEXT")
            columns.append((name, tt.value))
            nxt = self._next()
            if nxt.kind == RPAREN:
                break
            if nxt.kind != COMMA:
                raise ValueError("expected ',' or ')' in column list")
        if not columns:
            raise ValueError("CREATE TABLE requires at least one column")
        return CreateTable(table, columns)

    # --- INSERT ------------------------------------------------------------
    def _parse_insert(self) -> Insert:
        self._eat_kw("INSERT")
        self._eat_kw("INTO")
        table = self._expect_ident()
        columns = None
        if self._peek().kind == LPAREN:
            self._next()
            columns = []
            while True:
                columns.append(self._expect_ident())
                nxt = self._next()
                if nxt.kind == RPAREN:
                    break
                if nxt.kind != COMMA:
                    raise ValueError("expected ',' or ')' in column list")
        self._eat_kw("VALUES")
        self._expect(LPAREN)
        values: list = []
        while True:
            values.append(self._parse_literal())
            nxt = self._next()
            if nxt.kind == RPAREN:
                break
            if nxt.kind != COMMA:
                raise ValueError("expected ',' or ')' in VALUES list")
        if not values:
            raise ValueError("VALUES list must be non-empty")
        return Insert(table, columns, values)

    def _parse_literal(self) -> Literal:
        t = self._next()
        if t.kind == INT:
            return Literal(t.value)
        if t.kind == STR:
            return Literal(t.value)
        if t.kind == NULL:
            return Literal(None)
        raise ValueError(f"expected a literal, got {t.kind} {t.value!r}")

    # --- SELECT ------------------------------------------------------------
    def _parse_select(self) -> Select:
        self._eat_kw("SELECT")
        distinct = False
        if self._at_kw("DISTINCT"):
            self._next()
            distinct = True

        if self._peek().kind == STAR:
            self._next()
            select_list: object = "*"
        else:
            select_list = self._parse_select_list()

        self._eat_kw("FROM")
        table = self._expect_ident()

        where = None
        if self._at_kw("WHERE"):
            self._next()
            where = self._parse_or()

        group_by = None
        if self._at_kw("GROUP"):
            self._next()
            self._eat_kw("BY")
            group_by = [self._expect_ident()]
            while self._peek().kind == COMMA:
                self._next()
                group_by.append(self._expect_ident())

        order_by = None
        if self._at_kw("ORDER"):
            self._next()
            self._eat_kw("BY")
            order_by = [self._parse_order_key()]
            while self._peek().kind == COMMA:
                self._next()
                order_by.append(self._parse_order_key())

        limit = None
        offset = None
        # LIMIT and OFFSET may appear in either order; each at most once.
        while self._at_kw("LIMIT", "OFFSET"):
            kw = self._next().value
            num = self._parse_count_literal()
            if kw == "LIMIT":
                if limit is not None:
                    raise ValueError("duplicate LIMIT")
                limit = num
            else:
                if offset is not None:
                    raise ValueError("duplicate OFFSET")
                offset = num

        return Select(distinct, select_list, table, where, group_by,
                      order_by, limit, offset)

    def _parse_count_literal(self) -> int:
        """LIMIT/OFFSET operand: an integer literal (sign allowed; range checked
        by the engine, which raises ValueError on negatives)."""
        t = self._next()
        if t.kind != INT:
            raise ValueError("LIMIT/OFFSET expects an integer")
        return t.value

    def _parse_order_key(self) -> OrderKey:
        col = self._expect_ident()
        descending = False
        if self._at_kw("ASC", "DESC"):
            descending = self._next().value == "DESC"
        return OrderKey(col, descending)

    def _parse_select_list(self) -> list:
        items = [self._parse_select_item()]
        while self._peek().kind == COMMA:
            self._next()
            items.append(self._parse_select_item())
        return items

    def _parse_select_item(self) -> SelectItem:
        start = self.pos
        expr = self._parse_select_expr()
        text = self._render(start, self.pos)
        alias = None
        if self._at_kw("AS"):
            self._next()
            alias = self._expect_ident()
        return SelectItem(expr, alias, text)

    def _parse_select_expr(self):
        t = self._peek()
        if t.kind == KW and t.value in ("COUNT", "SUM", "AVG", "MIN", "MAX"):
            func = self._next().value
            self._expect(LPAREN)
            if self._peek().kind == STAR:
                if func != "COUNT":
                    raise ValueError(f"{func}(*) is not allowed")
                self._next()
                arg = "*"
            else:
                arg = self._expect_ident()
            self._expect(RPAREN)
            return Aggregate(func, arg)
        if t.kind == IDENT:
            return Column(self._next().value)
        raise ValueError(f"invalid select item starting at {t.kind} {t.value!r}")

    def _render(self, start: int, end: int) -> str:
        """Reconstruct the exact source spelling of a select item from its
        tokens, e.g. ``COUNT(*)`` or ``col``. Used as the default result key."""
        parts: list[str] = []
        for tok in self.toks[start:end]:
            if tok.kind == STAR:
                parts.append("*")
            elif tok.kind == LPAREN:
                parts.append("(")
            elif tok.kind == RPAREN:
                parts.append(")")
            elif tok.kind in (KW, IDENT):
                parts.append(str(tok.value))
            else:  # pragma: no cover - select items only ever hold the above
                parts.append(str(tok.value))
        # COUNT ( * )  ->  COUNT(*)   ;  bare column stays as-is.
        out = ""
        for p in parts:
            if p == "(":
                out += "("
            elif p == ")":
                out += ")"
            else:
                out += p
        return out

    # --- WHERE condition grammar (precedence: OR < AND < NOT < primary) ----
    def _parse_or(self):
        node = self._parse_and()
        while self._at_kw("OR"):
            self._next()
            node = Or(node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_not()
        while self._at_kw("AND"):
            self._next()
            node = And(node, self._parse_not())
        return node

    def _parse_not(self):
        if self._at_kw("NOT"):
            self._next()
            return Not(self._parse_not())
        return self._parse_primary()

    def _parse_primary(self):
        if self._peek().kind == LPAREN:
            self._next()
            node = self._parse_or()
            self._expect(RPAREN)
            return node
        # A comparison: column-vs-literal in either order, or col IS [NOT] NULL.
        t = self._peek()
        if t.kind == IDENT:
            col = self._next().value
            if self._at_kw("IS"):
                self._next()
                negated = False
                if self._at_kw("NOT"):
                    self._next()
                    negated = True
                nt = self._next()
                if nt.kind != NULL:
                    raise ValueError("expected NULL after IS [NOT]")
                return IsNull(col, negated)
            op_tok = self._next()
            if op_tok.kind != OP:
                raise ValueError("expected a comparison operator")
            lit = self._parse_literal()
            return Compare(col, op_tok.value, lit.value)
        # literal OP column  (normalise to column-on-left with flipped op)
        if t.kind in (INT, STR, NULL):
            lit = self._parse_literal()
            op_tok = self._next()
            if op_tok.kind != OP:
                raise ValueError("expected a comparison operator")
            col = self._expect_ident()
            return Compare(col, _FLIP[op_tok.value], lit.value)
        raise ValueError(f"invalid condition at {t.kind} {t.value!r}")


def parse(sql: str):
    """Tokenize and parse one statement; raise ``ValueError`` if malformed."""
    return _Parser(tokenize(sql)).parse_statement()
