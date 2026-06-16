"""graph_engine.py — Facade: re-exports all public names from structures, traversal, ranking."""

import sys
import os

# Ensure the directory containing this file is on the path so sibling modules can be imported
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from structures import Graph
from traversal import bfs, dijkstra, connected_components
from ranking import pagerank, degree_centrality

__all__ = [
    "Graph",
    "bfs",
    "dijkstra",
    "connected_components",
    "pagerank",
    "degree_centrality",
]
