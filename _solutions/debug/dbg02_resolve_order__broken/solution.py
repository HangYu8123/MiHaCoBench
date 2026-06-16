"""Deliberately-broken reference for debug/dbg02_resolve_order.

Planted defect (mirrors the real c04_formula_engine cycle-detection failure): a
single ``visited`` set is used, so a node already marked visited is skipped on a
back-edge instead of being recognised as a cycle. Self-dependencies and direct
two-node cycles are therefore accepted silently (no ``ValueError``). Valid DAGs
still produce a correct order, so the defect is localized to cycle detection.
"""
from __future__ import annotations


def resolve_load_order(dependencies: dict[str, list[str]]) -> list[str]:
    order: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:  # cannot distinguish a back-edge from a finished node
            return
        visited.add(node)
        for dep in dependencies.get(node, []):
            visit(dep)
        order.append(node)

    for node in sorted(dependencies):
        visit(node)
    return order
