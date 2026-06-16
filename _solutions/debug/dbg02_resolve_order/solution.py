"""Gold reference for debug/dbg02_resolve_order — dependency load ordering (stdlib).

The original DFS used a single ``visited`` set, which cannot tell "already
finished" apart from "currently on the recursion path", so cyclic inputs
(including self-dependencies and direct two-node cycles) were silently accepted.
The fix tracks a per-node state — ``"visiting"`` while a node is on the current
path, ``"done"`` once finished — and raises ``ValueError`` on a back-edge.
"""
from __future__ import annotations


def resolve_load_order(dependencies: dict[str, list[str]]) -> list[str]:
    """Return a load order in which every module follows all of its dependencies.

    ``dependencies`` maps each module to the list of modules it depends on (which
    must load first); every referenced module also appears as a key. Raises
    ``ValueError`` if the dependency graph contains a cycle (a self-dependency or
    any directed cycle).
    """
    order: list[str] = []
    state: dict[str, str] = {}  # node -> "visiting" | "done"

    def visit(node: str) -> None:
        current = state.get(node)
        if current == "done":
            return
        if current == "visiting":
            raise ValueError(f"dependency cycle detected at {node!r}")
        state[node] = "visiting"
        for dep in dependencies.get(node, []):
            visit(dep)
        state[node] = "done"
        order.append(node)

    for node in sorted(dependencies):
        visit(node)
    return order
