"""
engine.py — Public facade for the reactive dataflow engine.

Exports:
    Engine — the main class for the reactive dataflow engine.
"""
from graph import DependencyGraph


class _Cell:
    """Internal representation of a cell (constant or formula)."""

    __slots__ = ("name", "is_formula", "value", "deps", "fn",
                 "cache_valid", "cached_value", "recompute_count")

    def __init__(self, name):
        self.name = name
        self.is_formula = False
        self.value = None       # for constant cells
        self.deps = []          # list of dep names for formula cells
        self.fn = None          # callable for formula cells
        self.cache_valid = False
        self.cached_value = None
        self.recompute_count = 0


class Engine:
    """
    Reactive dataflow engine.

    Cells are either constants (set via set_value) or formulas
    (set via set_formula). Reads are lazy and memoized. When a cell's
    definition changes, it and all transitive dependents are invalidated.
    """

    def __init__(self):
        self._cells: dict = {}       # name -> _Cell
        self._graph = DependencyGraph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, name, value) -> None:
        """
        Define or replace a constant cell.
        Invalidates the cell's cache and all transitive dependents.
        """
        if name not in self._cells:
            self._cells[name] = _Cell(name)

        cell = self._cells[name]

        # If this was a formula cell, remove its dependency edges
        if cell.is_formula:
            self._graph.remove_dependencies(name)

        cell.is_formula = False
        cell.value = value
        cell.deps = []
        cell.fn = None

        # Ensure the node exists in the graph
        self._graph.ensure_node(name)

        # Invalidate this cell and all transitive dependents
        self._invalidate(name)

    def set_formula(self, name, deps: list, fn) -> None:
        """
        Define or replace a formula cell.
        Raises ValueError (with rollback) if this would create a cycle.
        Invalidates the cell and all transitive dependents.
        """
        # Save previous state for rollback on non-graph errors
        prev_cell = self._cells.get(name)

        # Attempt to update the graph (raises ValueError on cycle, with rollback)
        self._graph.set_dependencies(name, deps)

        # Graph update succeeded — update the cell
        if name not in self._cells:
            self._cells[name] = _Cell(name)

        cell = self._cells[name]
        cell.is_formula = True
        cell.value = None
        cell.deps = list(deps)
        cell.fn = fn

        # Invalidate this cell and all transitive dependents
        self._invalidate(name)

    def get(self, name):
        """
        Return the cell's value, computing lazily if the cache is dirty.
        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(name)

        cell = self._cells[name]

        if not cell.is_formula:
            # Constant cells are always "valid" — their value is just the stored value
            return cell.value

        # Formula cell
        if cell.cache_valid:
            return cell.cached_value

        # Recompute
        dep_values = [self.get(d) for d in cell.deps]
        result = cell.fn(*dep_values)
        cell.cached_value = result
        cell.cache_valid = True
        cell.recompute_count += 1
        return result

    def recompute_count(self, name) -> int:
        """
        Return how many times `name` has actually been (re)computed.
        Raises KeyError for unknown names.
        """
        if name not in self._cells:
            raise KeyError(name)
        return self._cells[name].recompute_count

    def batch(self, updates: dict) -> None:
        """
        Apply several set_value updates atomically.
        All affected cells are invalidated once (set-based), not per-edge.
        """
        # Collect all cells that need invalidation
        all_to_invalidate = set()

        for name, value in updates.items():
            if name not in self._cells:
                self._cells[name] = _Cell(name)

            cell = self._cells[name]

            # If this was a formula cell, remove its dependency edges
            if cell.is_formula:
                self._graph.remove_dependencies(name)

            cell.is_formula = False
            cell.value = value
            cell.deps = []
            cell.fn = None

            # Ensure the node exists in the graph
            self._graph.ensure_node(name)

            # Collect the cell itself and its transitive dependents
            all_to_invalidate.add(name)
            all_to_invalidate.update(self._graph.get_transitive_dependents(name))

        # Invalidate all affected cells once (set-based)
        for cell_name in all_to_invalidate:
            if cell_name in self._cells:
                cell = self._cells[cell_name]
                if cell.is_formula:
                    cell.cache_valid = False
                    cell.cached_value = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _invalidate(self, name) -> None:
        """
        Invalidate the cache of `name` and all transitive dependents.
        For the cell itself: if it's a formula, mark dirty.
        For transitive dependents: mark their caches dirty.
        """
        # The cell itself
        if name in self._cells:
            cell = self._cells[name]
            if cell.is_formula:
                cell.cache_valid = False
                cell.cached_value = None

        # All transitive dependents
        dependents = self._graph.get_transitive_dependents(name)
        for dep_name in dependents:
            if dep_name in self._cells:
                dep_cell = self._cells[dep_name]
                if dep_cell.is_formula:
                    dep_cell.cache_valid = False
                    dep_cell.cached_value = None
