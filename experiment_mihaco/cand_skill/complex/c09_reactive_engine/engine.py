"""
engine.py — Reactive Dataflow Engine (public facade).

Public API:
    Engine()
    engine.set_value(name, value)
    engine.set_formula(name, deps, fn)
    engine.get(name)
    engine.recompute_count(name)
    engine.batch(updates)

Semantics:
- Edges in the dependency graph go  dep -> dependent  (same as the rest of
  the codebase: nx.descendants gives transitive dependents).
- Reads are lazy + memoized; dirty flag drives recomputation.
- Cycles are rejected atomically (engine left unchanged on ValueError).
- batch() invalidates via set-union to guarantee at-most-one recompute.
"""

import copy

from graph import DependencyGraph


class Engine:
    """
    Reactive dataflow engine.

    _cells maps  name -> dict with keys:
        type    : 'const' | 'formula'
        value   : cached / stored value  (for const: always set; for formula: last computed)
        fn      : callable               (formula only)
        deps    : list of dependency names (formula only)
        dirty   : bool — True if cache is invalid
        count   : int  — number of actual recomputations
    """

    def __init__(self):
        self._graph = DependencyGraph()
        self._cells: dict = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mark_dirty(self, names):
        """Mark every name in *names* as dirty (if it exists)."""
        for n in names:
            if n in self._cells:
                self._cells[n]['dirty'] = True

    def _invalidate(self, name):
        """
        Mark *name* and ALL transitive dependents dirty.
        Called after a cell definition changes.
        """
        affected = {name} | self._graph.transitive_dependents(name)
        self._mark_dirty(affected)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, name, value):
        """
        Define/replace *name* as a constant cell.

        If *name* was previously a formula cell, remove its incoming
        dependency edges from the graph (so those deps no longer list
        *name* as a dependent).  We do NOT remove outgoing edges (cells
        that depend on *name*) because they still legitimately depend on
        this cell.
        """
        old = self._cells.get(name)

        # If switching FROM formula: remove the formula's dep->name edges
        if old is not None and old['type'] == 'formula':
            self._graph.remove_incoming_edges(name)

        # Ensure node exists in the graph (may have dependents already)
        self._graph.ensure_node(name)

        # Write cell
        self._cells[name] = {
            'type': 'const',
            'value': value,
            'dirty': False,  # const cells are always clean
            'count': 0 if old is None else old.get('count', 0),
        }

        # Invalidate transitive dependents (not the cell itself — it's const)
        dependents = self._graph.transitive_dependents(name)
        self._mark_dirty(dependents)

    def set_formula(self, name, deps: list, fn):
        """
        Define/replace *name* as a computed cell.

        Atomically:
          1. Snapshot old cell and old graph edges.
          2. Attempt to update graph edges (raises ValueError on cycle).
          3. On failure: graph is already restored by DependencyGraph.add_edges;
             restore cell snapshot.
          4. On success: update cell definition, invalidate transitive
             dependents.
        """
        old_cell = copy.copy(self._cells.get(name))  # shallow copy or None

        # Attempt graph mutation — raises ValueError and self-restores on cycle
        try:
            self._graph.add_edges(name, deps)
        except ValueError:
            # Graph already rolled back inside add_edges.
            # Restore cell if it was modified (it hasn't been yet, but be safe).
            if old_cell is None and name in self._cells:
                del self._cells[name]
            elif old_cell is not None:
                self._cells[name] = old_cell
            raise  # re-raise unchanged

        # Graph updated successfully — write cell definition
        old_count = old_cell.get('count', 0) if old_cell is not None else 0
        self._cells[name] = {
            'type': 'formula',
            'value': None,    # no cached value yet
            'fn': fn,
            'deps': list(deps),
            'dirty': True,    # must recompute on next get
            'count': old_count,
        }

        # Invalidate transitive dependents
        dependents = self._graph.transitive_dependents(name)
        self._mark_dirty(dependents)

    def get(self, name):
        """
        Return the cell's value, recomputing lazily if dirty.
        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(name)

        cell = self._cells[name]

        if cell['type'] == 'const':
            # Constant cells are never dirty; value is always current.
            return cell['value']

        # Formula cell
        if cell['dirty'] or cell['value'] is None:
            # Lazily compute by recursing into dependencies
            args = [self.get(d) for d in cell['deps']]
            cell['value'] = cell['fn'](*args)
            cell['dirty'] = False
            cell['count'] += 1

        return cell['value']

    def recompute_count(self, name):
        """
        Return how many times *name* has actually been recomputed.
        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(name)
        return self._cells[name]['count']

    def batch(self, updates: dict):
        """
        Apply several set_value updates atomically.

        Invalidation is set-based: compute the full union of affected
        cells FIRST (so each affected formula cell is marked dirty
        exactly once), then write the values.

        This guarantees at-most-one recompute per affected cell on
        subsequent get() calls.
        """
        # 1. Compute full set of cells to invalidate BEFORE writing anything.
        affected: set = set()
        for name in updates:
            affected.add(name)
            affected |= self._graph.transitive_dependents(name)

        # 2. Write all constant values (set_value also marks dependents dirty,
        #    but we'll do our own authoritative invalidation pass right after).
        for name, value in updates.items():
            # Inline set_value logic but WITHOUT calling _invalidate again
            # to avoid double-counting.
            old = self._cells.get(name)
            if old is not None and old['type'] == 'formula':
                self._graph.remove_incoming_edges(name)
            self._graph.ensure_node(name)
            self._cells[name] = {
                'type': 'const',
                'value': value,
                'dirty': False,
                'count': 0 if old is None else old.get('count', 0),
            }

        # 3. Mark the full affected set dirty (the keys themselves are const
        #    so dirty=False for them; only formula cells in the affected set
        #    get marked dirty, which is what we want).
        for n in affected:
            if n in self._cells and self._cells[n]['type'] == 'formula':
                self._cells[n]['dirty'] = True
