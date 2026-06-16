"""
engine.py — Public facade for the reactive dataflow engine.

Implements `Engine` class which manages a reactive graph of named cells:
- Constant cells hold a value directly.
- Formula cells compute their value from other cells' values.

Reads are lazy and memoized; changing a cell invalidates it and all transitive dependents.
"""

from graph import DependencyGraph


class _ConstantCell:
    """A cell holding a constant value."""

    def __init__(self, value):
        self.value = value
        self.is_formula = False


class _FormulaCell:
    """A cell computed from a formula applied to dependencies."""

    def __init__(self, deps, fn):
        self.deps = list(deps)
        self.fn = fn
        self.is_formula = True
        self.cached_value = None
        self.dirty = True


class Engine:
    """
    Reactive dataflow engine.

    Cells are either constants or formulas. Formula values are lazily computed
    and memoized. Updating a cell invalidates it and all transitive dependents.
    """

    def __init__(self):
        self._graph = DependencyGraph()
        # _cells maps name -> _ConstantCell or _FormulaCell
        self._cells = {}
        # _cache maps name -> cached value (for constants, always valid; for formulas, when not dirty)
        self._cache = {}
        # _dirty: set of formula cell names whose cache is stale
        self._dirty = set()
        # _recompute_count: number of times each formula cell has been recomputed
        self._recompute_count = {}

    def set_value(self, name, value):
        """
        Define or replace a constant cell holding `value`.
        Invalidates the cell and all transitive dependents.
        """
        # Get transitive dependents BEFORE changing the graph structure
        # (if name already exists as a formula, remove its dependency edges first)
        if name in self._cells and self._cells[name].is_formula:
            self._graph.remove_dependencies(name)

        # Ensure node exists in graph
        self._graph.add_node(name)

        # Compute transitive dependents before any change
        transitive_deps = self._graph.get_transitive_dependents(name)

        # Set constant cell
        self._cells[name] = _ConstantCell(value)
        self._cache[name] = value

        # Ensure recompute_count entry exists (constants don't have recompute counts
        # but we need KeyError behavior for get() and recompute_count() only when never defined)
        if name not in self._recompute_count:
            self._recompute_count[name] = 0

        # Invalidate all transitive dependents
        for dep in transitive_deps:
            if dep in self._cells and self._cells[dep].is_formula:
                self._dirty.add(dep)

    def set_formula(self, name, deps, fn):
        """
        Define or replace a formula cell.
        The cell's value is fn(*[get(d) for d in deps]).
        Raises ValueError if introducing a cycle.
        """
        # Ensure node exists
        self._graph.add_node(name)

        # This may raise ValueError and rollback if cycle detected
        self._graph.set_dependencies(name, deps)

        # Ensure all dep nodes exist
        for dep in deps:
            self._graph.add_node(dep)

        # Get transitive dependents (including `name` itself is dirty)
        transitive_deps = self._graph.get_transitive_dependents(name)

        # Set the formula cell
        cell = _FormulaCell(deps, fn)
        self._cells[name] = cell

        # Initialize recompute count if first time
        if name not in self._recompute_count:
            self._recompute_count[name] = 0

        # Mark name itself dirty (its definition changed)
        self._dirty.add(name)

        # Invalidate transitive dependents
        for dep in transitive_deps:
            if dep in self._cells and self._cells[dep].is_formula:
                self._dirty.add(dep)

    def get(self, name):
        """
        Return the cell's current value, recomputing lazily if dirty.
        Raises KeyError if name is unknown.
        """
        if name not in self._cells:
            raise KeyError(f"Unknown cell: {name!r}")

        cell = self._cells[name]

        if not cell.is_formula:
            # Constant cell: always clean
            return self._cache[name]

        # Formula cell
        if name not in self._dirty:
            # Cache is clean
            return self._cache[name]

        # Need to recompute
        dep_values = [self.get(d) for d in cell.deps]
        result = cell.fn(*dep_values)
        self._cache[name] = result
        self._dirty.discard(name)
        self._recompute_count[name] += 1
        return result

    def recompute_count(self, name):
        """
        Return how many times `name` has been recomputed.
        Raises KeyError if name is unknown.
        """
        if name not in self._cells:
            raise KeyError(f"Unknown cell: {name!r}")
        return self._recompute_count.get(name, 0)

    def batch(self, updates):
        """
        Apply multiple set_value updates atomically.
        Each affected cell recomputes at most once on the next reads.
        Invalidation is set-based (not per-edge).
        """
        # Collect all transitive dependents across all updated cells
        all_dirty = set()

        for name, value in updates.items():
            # Remove formula dependencies if switching from formula to constant
            if name in self._cells and self._cells[name].is_formula:
                self._graph.remove_dependencies(name)

            # Ensure node exists
            self._graph.add_node(name)

            # Collect transitive dependents
            transitive_deps = self._graph.get_transitive_dependents(name)
            all_dirty.update(transitive_deps)

            # Set constant cell
            self._cells[name] = _ConstantCell(value)
            self._cache[name] = value

            if name not in self._recompute_count:
                self._recompute_count[name] = 0

        # Mark all transitive dependents as dirty (set-based, not per-edge)
        for dep in all_dirty:
            if dep in self._cells and self._cells[dep].is_formula:
                self._dirty.add(dep)
