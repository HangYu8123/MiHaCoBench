"""Public facade for the in-memory mini-SQL engine (gold reference).

The grader imports this module and uses only the :class:`Database` class. The
actual work is split across sibling modules:

* :mod:`tokenizer` — lexes a statement into tokens,
* :mod:`sqlparser` — recursive-descent parser producing a statement AST,
* :mod:`engine`   — owns the tables and executes the AST with full semantics.

``Database`` is a thin wrapper so the multi-file structure stays invisible to
callers; everything flows through :meth:`Database.execute`.
"""
from __future__ import annotations

from engine import Engine


class Database:
    """An in-memory SQL database supporting CREATE/INSERT/SELECT."""

    def __init__(self) -> None:
        self._engine = Engine()

    def execute(self, sql: str):
        """Run one SQL statement.

        ``SELECT`` returns a ``list[dict]`` (column/alias -> value) in result
        order; every other statement returns ``None``. Raises ``ValueError`` on
        any malformed statement, unknown table/column, type mismatch, invalid
        GROUP BY, or negative LIMIT/OFFSET.
        """
        return self._engine.execute(sql)
