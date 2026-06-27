def resolve_load_order(dependencies: dict[str, list[str]]) -> list[str]:
    """Return a valid topological load order for the given dependency graph.

    Raises ValueError if the graph contains any cycle (including self-loops).
    """
    order = []
    visited = set()   # BLACK: fully processed nodes
    in_stack = set()  # GREY: nodes currently on the active DFS call stack

    def visit(node):
        if node in visited:
            return
        if node in in_stack:
            raise ValueError(f"Cycle detected involving node: {node!r}")
        in_stack.add(node)
        for dep in dependencies.get(node, []):
            visit(dep)
        in_stack.discard(node)
        visited.add(node)
        order.append(node)

    for node in sorted(dependencies):
        visit(node)
    return order
