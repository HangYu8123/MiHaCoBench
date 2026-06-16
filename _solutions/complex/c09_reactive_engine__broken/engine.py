"""Reactive dataflow engine — public facade (c09_reactive_engine).

BROKEN VARIANT. The planted defect lives in invalidation propagation: when a
constant cell changes (:meth:`Engine.set_value` / :meth:`Engine.batch`), only the
changed cell itself is touched — its **transitive dependents are NOT invalidated**.
Their memoized caches therefore go stale, so a downstream formula read after an
input update returns the OLD result.

Direct dependents that have never been computed yet still compute correctly on
their first read (they were already dirty), so the basic happy-path tests pass; it
is the *transitive cache invalidation* contract that is violated.
"""
from __future__ import annotations

from typing import Any, Callable

from graph import DependencyGraph


class _Cell:
    """Internal record for one cell (see the gold module for full docs)."""

    __slots__ = ("kind", "value", "deps", "fn", "cache", "clean", "recomputes")

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.value: Any = None
        self.deps: list[Any] = []
        self.fn: Callable[..., Any] | None = None
        self.cache: Any = None
        self.clean: bool = False
        self.recomputes: int = 0


class Engine:
    """A lazy, memoizing reactive computation graph with cycle detection."""

    def __init__(self) -> None:
        self._cells: dict[Any, _Cell] = {}
        self._graph = DependencyGraph()

    # ------------------------------------------------------------------ #
    # Definition
    # ------------------------------------------------------------------ #

    def set_value(self, name: Any, value: Any) -> None:
        """Define or replace constant cell *name* holding *value*."""
        cell = self._cells.get(name)
        if cell is None or cell.kind != "const":
            cell = _Cell("const")
            self._cells[name] = cell
        self._graph.add_cell(name)
        self._graph.clear_dependencies(name)
        cell.kind = "const"
        cell.deps = []
        cell.fn = None
        cell.value = value
        cell.cache = value
        cell.clean = True
        # BUG: only `name` itself is updated here; the transitive dependents
        # keep their stale memoized caches and are never marked dirty.

    def set_formula(self, name: Any, deps: list[Any], fn: Callable[..., Any]) -> None:
        """Define or replace computed cell *name* = ``fn(*[get(d) for d in deps])``."""
        deps = list(deps)
        old = self._cells.get(name)

        self._graph.add_cell(name)
        for d in deps:
            self._graph.add_cell(d)

        # Raises ValueError (mutating nothing) if a cycle would form.
        self._graph.set_dependencies(name, deps)

        cell = old if (old is not None) else _Cell("formula")
        if old is None:
            self._cells[name] = cell
        cell.kind = "formula"
        cell.deps = deps
        cell.fn = fn
        cell.value = None
        cell.cache = None
        cell.clean = False
        self._invalidate_dependents(name)

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #

    def get(self, name: Any) -> Any:
        """Return the value of cell *name*, recomputing lazily if its cache is dirty."""
        cell = self._cells.get(name)
        if cell is None:
            raise KeyError(name)
        if cell.clean:
            return cell.cache
        return self._recompute(name, cell)

    def recompute_count(self, name: Any) -> int:
        """Number of times *name* has actually been (re)computed since creation."""
        cell = self._cells.get(name)
        if cell is None:
            raise KeyError(name)
        return cell.recomputes

    # ------------------------------------------------------------------ #
    # Batch
    # ------------------------------------------------------------------ #

    def batch(self, updates: dict) -> None:
        """Apply several :meth:`set_value` updates atomically."""
        for name, value in updates.items():
            cell = self._cells.get(name)
            if cell is None or cell.kind != "const":
                cell = _Cell("const")
                self._cells[name] = cell
            self._graph.add_cell(name)
            self._graph.clear_dependencies(name)
            cell.kind = "const"
            cell.deps = []
            cell.fn = None
            cell.value = value
            cell.cache = value
            cell.clean = True
        # BUG: same defect as set_value — transitive dependents are not
        # invalidated, so downstream formulas keep stale memoized caches.

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _invalidate_dependents(self, name: Any) -> None:
        """Mark every transitive dependent of *name* dirty (set-based)."""
        for n in self._graph.dependents(name):
            c = self._cells.get(n)
            if c is not None and c.kind == "formula":
                c.clean = False

    def _recompute(self, name: Any, cell: _Cell) -> Any:
        """Compute (and memoize) *cell*'s value, recursing through dependencies."""
        if cell.kind == "const":
            cell.cache = cell.value
            cell.clean = True
            return cell.cache
        args = [self.get(d) for d in cell.deps]
        assert cell.fn is not None
        result = cell.fn(*args)
        cell.cache = result
        cell.clean = True
        cell.recomputes += 1
        return result
