def resolve_load_order(dependencies: dict[str, list[str]]) -> list[str]:
    order = []
    done = set()
    in_progress = set()

    def visit(node):
        if node in done:
            return
        if node in in_progress:
            raise ValueError("Cycle detected")
        in_progress.add(node)
        for dep in dependencies.get(node, []):
            visit(dep)
        in_progress.discard(node)
        done.add(node)
        order.append(node)

    for node in sorted(dependencies):
        visit(node)
    return order
