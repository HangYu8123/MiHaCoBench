"""
engine.py — Public facade: defines the Engine class.

Imports from graph.py (same directory) for dependency-graph operations.
"""
import sys
import os

# Ensure graph.py is importable regardless of the working directory
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from graph import DependencyGraph


class Engine:
    """
    Reactive dataflow engine.

    Cells are either *constant* (set_value) or *computed* (set_formula).
    Reads are lazy and memoized.  Changing a cell's definition invalidates its
    cached value and the cached values of all transitive dependents.
    """

    def __init__(self):
        # name -> {type, value, fn, deps, dirty, count}
        self._cells: dict = {}
        self._graph = DependencyGraph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, name, value) -> None:
        """
        Define or replace a constant cell.

        If the cell was previously a formula cell, remove its formula edges
        from the dependency graph so stale edges do not linger.
        Marks the cell and all transitive dependents as dirty.
        """
        # If the cell previously had formula deps, remove them from the graph
        if name in self._cells and self._cells[name]['type'] == 'formula':
            self._graph.remove_formula_edges(name)

        # Ensure node exists in graph (so descendants query works)
        self._graph.ensure_node(name)

        # Compute which cells need to be invalidated BEFORE writing
        transitive = self._graph.get_transitive_dependents(name)

        # Create or update the cell entry
        if name in self._cells:
            # Preserve count when switching types — spec is silent on reset
            existing_count = self._cells[name]['count']
        else:
            existing_count = 0

        self._cells[name] = {
            'type': 'value',
            'value': value,
            'fn': None,
            'deps': [],
            'dirty': False,   # constant cells are never dirty themselves
            'count': existing_count,
        }

        # Mark transitive dependents dirty
        for dep_name in transitive:
            if dep_name in self._cells:
                self._cells[dep_name]['dirty'] = True

    def set_formula(self, name, deps: list, fn) -> None:
        """
        Define or replace a computed cell.

        Raises ValueError (with no side-effects) if the new deps would
        introduce a cycle in the dependency graph.
        """
        # Attempt to update the graph — raises ValueError on cycle,
        # leaving the graph unchanged.
        self._graph.ensure_node(name)
        self._graph.add_or_update_formula(name, deps)

        # Graph update succeeded — now update the cell dict.
        existing_count = self._cells[name]['count'] if name in self._cells else 0

        self._cells[name] = {
            'type': 'formula',
            'value': None,       # cache starts empty / dirty
            'fn': fn,
            'deps': list(deps),
            'dirty': True,
            'count': existing_count,
        }

        # Invalidate transitive dependents
        transitive = self._graph.get_transitive_dependents(name)
        for dep_name in transitive:
            if dep_name in self._cells:
                self._cells[dep_name]['dirty'] = True

    def get(self, name):
        """
        Return the cell's value, recomputing lazily if the cache is dirty.

        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(name)

        cell = self._cells[name]

        if cell['type'] == 'formula' and cell['dirty']:
            # Recursively resolve dependencies (bottom-up via recursion)
            args = [self.get(d) for d in cell['deps']]
            cell['value'] = cell['fn'](*args)
            cell['dirty'] = False
            cell['count'] += 1

        return cell['value']

    def recompute_count(self, name) -> int:
        """
        Return how many times *name* has been (re)computed.

        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(name)
        return self._cells[name]['count']

    def batch(self, updates: dict) -> None:
        """
        Apply several set_value updates atomically.

        Invalidation is set-based: the union of all transitive dependents
        across all updated keys is computed ONCE before any values are written,
        then marked dirty in a single pass.
        """
        # 1. Pre-compute dirty set across ALL updated keys BEFORE writing
        dirty_set: set = set()
        for k in updates:
            # Remove old formula edges if cell was previously a formula
            if k in self._cells and self._cells[k]['type'] == 'formula':
                self._graph.remove_formula_edges(k)
            self._graph.ensure_node(k)
            dirty_set |= self._graph.get_transitive_dependents(k)

        # 2. Write all values (constant cells, never dirty themselves)
        for k, v in updates.items():
            existing_count = self._cells[k]['count'] if k in self._cells else 0
            self._cells[k] = {
                'type': 'value',
                'value': v,
                'fn': None,
                'deps': [],
                'dirty': False,
                'count': existing_count,
            }

        # 3. Mark the pre-computed dirty set (exclude the updated keys
        #    themselves, which are now fresh constant cells)
        for dep_name in dirty_set:
            if dep_name in self._cells:
                self._cells[dep_name]['dirty'] = True
