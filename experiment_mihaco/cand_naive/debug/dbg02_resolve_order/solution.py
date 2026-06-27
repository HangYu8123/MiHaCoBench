def resolve_load_order(dependencies: dict[str, list[str]]) -> list[str]:
    """Return a valid topological load order, or raise ValueError if a cycle exists."""
    order = []
    visited = set()   # fully processed nodes
    in_stack = set()  # nodes currently on the DFS recursion stack

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
