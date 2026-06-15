"""graph_engine — public facade for c03_graph_engine (BROKEN VARIANT).

Re-exports every public name from the four implementation modules.
BROKEN: dijkstra in traversal.py ignores edge weights (uses hop count).
"""
from __future__ import annotations

# Data structure
from structures import Graph  # noqa: F401

# Traversal + components (broken dijkstra inside)
from traversal import bfs, connected_components, dijkstra  # noqa: F401

# Ranking
from ranking import degree_centrality, pagerank  # noqa: F401

__all__ = [
    "Graph",
    "bfs",
    "dijkstra",
    "connected_components",
    "pagerank",
    "degree_centrality",
]
