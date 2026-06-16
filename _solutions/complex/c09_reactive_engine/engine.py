"""Reactive dataflow engine — public facade (c09_reactive_engine).

An ``Engine`` holds a set of named *cells*. A cell is either:

* a **constant** cell holding a fixed ``value`` (set via :meth:`Engine.set_value`), or
* a **computed** cell whose value is ``fn(*[get(d) for d in deps])`` over its
  dependency cells (defined via :meth:`Engine.set_formula`).

The engine is **lazy + memoizing**: :meth:`Engine.get` returns a cached value
without recomputation when the cache is clean, and recomputes (once) when the
cache is dirty, caching the fresh result. Whenever a cell's definition changes,
that cell **and all of its transitive dependents** are invalidated, so their next
:meth:`Engine.get` recomputes against the new inputs. Introducing a dependency
cycle raises :class:`ValueError` and leaves the engine unchanged.

The dependency bookkeeping lives in :mod:`graph` (a ``networkx`` DAG); this module
is the orchestration layer that ties caching, invalidation, lazy recompute and
cycle roll-back together.
"""
from __future__ import annotations

from typing import Any, Callable

from graph import DependencyGraph


class _Cell:
    """Internal record for one cell.

    Attributes
    ----------
    kind:
        ``"const"`` or ``"formula"``.
    value:
        The literal value (constant cells only).
    deps:
        Ordered dependency names (formula cells only).
    fn:
        The pure function combining the dependency values (formula cells only).
    cache:
        The last computed value (meaningful only when ``clean`` is ``True``).
    clean:
        ``True`` iff ``cache`` is up to date and may be returned without recompute.
    recomputes:
        How many times this cell has actually been (re)computed.
    """

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
        """Define or replace constant cell *name* holding *value*.

        Replacing a cell invalidates the cached value of *name* **and every cell
        that transitively depends on it**, so their next :meth:`get` recomputes.
        """
        cell = self._cells.get(name)
        if cell is None or cell.kind != "const":
            cell = _Cell("const")
            self._cells[name] = cell
        # A constant that used to be a formula must drop its dependency edges.
        self._graph.add_cell(name)
        self._graph.clear_dependencies(name)
        cell.kind = "const"
        cell.deps = []
        cell.fn = None
        cell.value = value
        # The constant's own value is known immediately — no recompute needed —
        # but its dependents are now stale.
        cell.cache = value
        cell.clean = True
        self._invalidate_dependents(name)

    def set_formula(self, name: Any, deps: list[Any], fn: Callable[..., Any]) -> None:
        """Define or replace computed cell *name* = ``fn(*[get(d) for d in deps])``.

        Registers edges ``dep -> name`` in the dependency graph. Replacing an
        existing formula re-points its dependencies. If the new edges would
        introduce a cycle, raises :class:`ValueError` and leaves the engine
        **unchanged**. After a successful (re)definition, *name* and all of its
        transitive dependents are invalidated.
        """
        deps = list(deps)

        # Snapshot the old definition so we can roll back on a cycle.
        old = self._cells.get(name)
        old_kind = old.kind if old is not None else None
        old_deps = list(old.deps) if old is not None else None
        old_fn = old.fn if old is not None else None
        old_value = old.value if old is not None else None

        self._graph.add_cell(name)
        for d in deps:
            self._graph.add_cell(d)

        # This raises ValueError (and mutates nothing) if a cycle would form.
        self._graph.set_dependencies(name, deps)

        cell = old if (old is not None) else _Cell("formula")
        if old is None:
            self._cells[name] = cell
        cell.kind = "formula"
        cell.deps = deps
        cell.fn = fn
        cell.value = None
        # A fresh/replaced formula starts dirty; its value is computed lazily.
        cell.cache = None
        cell.clean = False
        # Defensive: keep the old definition reachable for documentation only.
        _ = (old_kind, old_deps, old_fn, old_value)
        self._invalidate_dependents(name)

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #

    def get(self, name: Any) -> Any:
        """Return the value of cell *name*, recomputing lazily if its cache is dirty.

        A clean cache is returned directly (no recompute, no recompute-count bump).
        Unknown *name* raises :class:`KeyError`.
        """
        cell = self._cells.get(name)
        if cell is None:
            raise KeyError(name)
        if cell.clean:
            return cell.cache
        return self._recompute(name, cell)

    def recompute_count(self, name: Any) -> int:
        """Number of times *name* has actually been (re)computed since creation.

        A :meth:`get` served from a clean cache does **not** increment this.
        Unknown *name* raises :class:`KeyError`.
        """
        cell = self._cells.get(name)
        if cell is None:
            raise KeyError(name)
        return cell.recomputes

    # ------------------------------------------------------------------ #
    # Batch
    # ------------------------------------------------------------------ #

    def batch(self, updates: dict) -> None:
        """Apply several :meth:`set_value` updates atomically.

        All cells in *updates* are written first; the union of their transitive
        dependents is then invalidated **once** (set-based, not per-edge), so each
        affected cell recomputes at most once on the next reads. Recomputation on
        the subsequent :meth:`get` calls respects topological order of
        dependencies (a dependency is computed before any dependent that needs it).
        """
        # Write every constant first.
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

        # Compute the combined invalidation set ONCE (set semantics dedupes the
        # diamond case where two updated inputs share a downstream dependent).
        affected: set = set()
        for name in updates:
            affected |= self._graph.dependents(name)
        for n in affected:
            c = self._cells.get(n)
            if c is not None and c.kind == "formula":
                c.clean = False

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
        # Formula: evaluate dependencies (which recurse lazily) then apply fn.
        args = [self.get(d) for d in cell.deps]
        assert cell.fn is not None
        result = cell.fn(*args)
        cell.cache = result
        cell.clean = True
        cell.recomputes += 1
        return result
