"""Dependency-graph tracking for the reactive dataflow engine (c09_reactive_engine).

A thin, well-tested wrapper around a ``networkx.DiGraph`` that stores one node
per cell and one edge ``dep -> name`` for every dependency ``dep`` of a computed
cell ``name``. Orienting the edges this way (from a dependency *toward* the cell
that consumes it) means that ``networkx.descendants(graph, x)`` is exactly the
set of cells whose cached value becomes stale when ``x`` changes — the transitive
dependents — which the engine relies on for cache invalidation.

The wrapper is deliberately side-effect-free on failure: :meth:`set_dependencies`
validates a candidate edge set against a *scratch* copy first, so an edit that
would introduce a cycle leaves the live graph untouched (the engine can then roll
the whole edit back and raise without corrupting its state).
"""
from __future__ import annotations

from typing import Any, Iterable

import networkx as nx


class DependencyGraph:
    """Tracks ``dep -> name`` edges for cells and answers reachability queries.

    Every cell (constant or computed) is a node. Only computed cells own outgoing
    *dependency* edges; the edge ``d -> n`` means "``n`` reads ``d``", so a change
    to ``d`` flows forward along edges to ``n`` and everything beyond it.
    """

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #

    def add_cell(self, name: Any) -> None:
        """Register *name* as a node; no-op if it already exists."""
        if not self._g.has_node(name):
            self._g.add_node(name)

    def has_cell(self, name: Any) -> bool:
        """Return ``True`` iff *name* is a known cell."""
        return self._g.has_node(name)

    def set_dependencies(self, name: Any, deps: Iterable[Any]) -> None:
        """Re-point *name*'s incoming dependency edges to exactly *deps*.

        Replaces any previously-registered dependencies of *name*. The candidate
        graph is validated on a scratch copy first: if the new edges would make
        the dependency graph cyclic, a ``ValueError`` is raised and **the live
        graph is left unchanged**.
        """
        deps = list(deps)

        # Validate on a scratch copy so a rejected edit has no side effects.
        scratch = self._g.copy()
        if not scratch.has_node(name):
            scratch.add_node(name)
        # Drop old dependency edges of `name`, then add the new ones.
        for pred in list(scratch.predecessors(name)):
            scratch.remove_edge(pred, name)
        for d in deps:
            if not scratch.has_node(d):
                scratch.add_node(d)
            scratch.add_edge(d, name)
        if not nx.is_directed_acyclic_graph(scratch):
            raise ValueError(
                f"setting dependencies {deps!r} for cell {name!r} introduces a cycle"
            )

        # Commit: the scratch copy is already the desired final state.
        self._g = scratch

    def clear_dependencies(self, name: Any) -> None:
        """Remove all incoming dependency edges of *name* (it becomes a leaf)."""
        if not self._g.has_node(name):
            return
        for pred in list(self._g.predecessors(name)):
            self._g.remove_edge(pred, name)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def dependents(self, name: Any) -> set:
        """Return the **transitive** dependents of *name* (excludes *name*).

        These are every cell whose cached value must be invalidated when *name*
        changes. Implemented with :func:`networkx.descendants`.
        """
        if not self._g.has_node(name):
            return set()
        return set(nx.descendants(self._g, name))

    def dependencies(self, name: Any) -> set:
        """Return the *direct* dependencies of *name* (its in-neighbours)."""
        if not self._g.has_node(name):
            return set()
        return set(self._g.predecessors(name))

    def topological_order(self, names: Iterable[Any]) -> list:
        """Return *names* ordered so that every dependency precedes its dependent.

        Uses a global topological sort of the DAG and filters it down to the
        requested set, preserving dependency-before-dependent order.
        """
        wanted = set(names)
        order = [n for n in nx.topological_sort(self._g) if n in wanted]
        # Any requested name not present as a node (defensive) is appended.
        for n in names:
            if n not in self._g and n not in order:
                order.append(n)
        return order
