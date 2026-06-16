"""
engine.py — Public facade for the reactive dataflow engine.

Implements the Engine class with:
  - set_value(name, value): define/replace a constant cell
  - set_formula(name, deps, fn): define/replace a computed cell
  - get(name): lazy memoized read
  - recompute_count(name): number of actual recomputations
  - batch(updates: dict): atomic multi-cell set_value
"""

from graph import Graph


class Engine:
    """
    Reactive dataflow engine.

    Cell structure in self._cells[name]:
        {
            'kind': 'value' | 'formula',
            'value': <cached value or constant>,
            'deps': [...],   # for formula cells
            'fn': <callable> | None,
            'dirty': bool,
            'count': int,    # recompute count
        }
    """

    def __init__(self):
        self._graph = Graph()
        self._cells = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, name, value) -> None:
        """
        Define/replace a constant cell holding `value`.
        Invalidates the cell and all transitive dependents.
        """
        # Ensure node exists in graph
        self._graph.ensure_node(name)

        # Remove old incoming edges (if this was a formula cell with deps)
        # Old outgoing edges (where name was a dep of something else) stay —
        # those represent other cells depending on `name`, which is correct.
        self._graph.remove_outgoing_edges(name)

        # Store the cell as a constant
        existing_count = self._cells.get(name, {}).get('count', 0)
        self._cells[name] = {
            'kind': 'value',
            'value': value,
            'deps': [],
            'fn': None,
            'dirty': False,  # constants are never dirty
            'count': existing_count,
        }

        # Invalidate all transitive dependents
        dependents = self._graph.get_descendants(name)
        for dep_name in dependents:
            if dep_name in self._cells:
                self._cells[dep_name]['dirty'] = True

    def set_formula(self, name, deps: list, fn) -> None:
        """
        Define/replace a computed cell.
        Raises ValueError if a cycle would be introduced.
        On cycle, leaves engine unchanged (full rollback).
        """
        # Take snapshot of graph before any changes
        graph_snapshot = self._graph.copy_graph_state()

        # Check if adding these deps would create a cycle
        # We need to simulate: remove old incoming edges for `name`, then add new ones
        # For cycle detection, work on a copy
        import networkx as nx

        g_copy = graph_snapshot.copy()

        # Ensure name exists
        if name not in g_copy:
            g_copy.add_node(name)

        # Remove old incoming edges to `name` (its current dependencies)
        old_preds = list(g_copy.predecessors(name))
        for pred in old_preds:
            g_copy.remove_edge(pred, name)

        # Add new edges dep -> name
        for dep in deps:
            if dep not in g_copy:
                g_copy.add_node(dep)
            g_copy.add_edge(dep, name)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(g_copy):
            raise ValueError(
                f"Setting formula for '{name}' with deps {deps} would create a cycle."
            )

        # No cycle — commit the graph changes
        self._graph.restore_graph_state(g_copy)

        # Save old cell state for rollback if needed (though graph check passed)
        # Update cell metadata
        existing_count = self._cells.get(name, {}).get('count', 0)
        self._cells[name] = {
            'kind': 'formula',
            'value': None,
            'deps': list(deps),
            'fn': fn,
            'dirty': True,  # formula cells start dirty (need recompute)
            'count': existing_count,
        }

        # Invalidate all transitive dependents of `name`
        dependents = self._graph.get_descendants(name)
        for dep_name in dependents:
            if dep_name in self._cells:
                self._cells[dep_name]['dirty'] = True

    def get(self, name):
        """
        Return the cell's value, recomputing lazily if dirty.
        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(f"Cell '{name}' is not defined.")

        cell = self._cells[name]

        if cell['kind'] == 'value':
            # Constants are always clean
            return cell['value']

        # Formula cell
        if not cell['dirty']:
            # Cache is clean, return memoized value
            return cell['value']

        # Dirty formula — recompute
        dep_values = [self.get(d) for d in cell['deps']]
        result = cell['fn'](*dep_values)

        # Cache the result
        cell['value'] = result
        cell['dirty'] = False
        cell['count'] += 1

        return result

    def recompute_count(self, name) -> int:
        """
        Return how many times `name` has been actually recomputed.
        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(f"Cell '{name}' is not defined.")
        return self._cells[name]['count']

    def batch(self, updates: dict) -> None:
        """
        Apply several set_value updates atomically.
        Invalidation is set-based — each affected cell is marked dirty at most once.
        """
        # Collect the union of all transitive dependent sets BEFORE writing
        # (graph structure doesn't change in batch — only values change)
        all_affected = set()
        for name in updates:
            self._graph.ensure_node(name)
            all_affected.add(name)
            all_affected |= self._graph.get_descendants(name)

        # Write all values atomically
        for name, value in updates.items():
            # Remove incoming edges (in case this was a formula cell)
            self._graph.remove_outgoing_edges(name)
            existing_count = self._cells.get(name, {}).get('count', 0)
            self._cells[name] = {
                'kind': 'value',
                'value': value,
                'deps': [],
                'fn': None,
                'dirty': False,
                'count': existing_count,
            }

        # Mark all affected dependents dirty (set-based, no double counting)
        for dep_name in all_affected:
            if dep_name in updates:
                # These are constants — they're already clean
                continue
            if dep_name in self._cells:
                self._cells[dep_name]['dirty'] = True
