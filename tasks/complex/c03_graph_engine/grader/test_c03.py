"""Grader for complex/c03_graph_engine. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant has dijkstra ignore weights (using hop count), causing the
weighted-distance test to fail.

Tests (>=8):
 1.  test_graph_basic_properties          — num_nodes, num_edges for undirected
 2.  test_graph_directed_basic            — directed graph edge count
 3.  test_bfs_hop_distances              — exact hop distances
 4.  test_bfs_source_zero               — source always maps to 0
 5.  test_bfs_disconnected              — unreachable nodes omitted
 6.  test_dijkstra_weighted_path        — shortest path differs from fewest hops
 7.  test_dijkstra_source_zero         — source always maps to 0.0
 8.  test_dijkstra_single_node         — trivial graph
 9.  test_connected_components_two     — undirected graph with 2 components
 10. test_connected_components_single  — single connected component
 11. test_pagerank_sums_to_one        — PR values sum to 1
 12. test_pagerank_vs_networkx        — cross-check against networkx within 1e-3
 13. test_degree_centrality_values    — exact degree centrality for a star graph
 14. test_degree_centrality_directed  — directed total degree
 15. advisory code_quality test
"""
from __future__ import annotations

import pytest
import networkx as nx

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c03_graph_engine"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load all public callables from the facade graph_engine.py
_mod = gu.load_module(SOL, "graph_engine.py", alias="graph_engine")
Graph = getattr(_mod, "Graph")
bfs = getattr(_mod, "bfs")
dijkstra = getattr(_mod, "dijkstra")
connected_components = getattr(_mod, "connected_components")
pagerank = getattr(_mod, "pagerank")
degree_centrality = getattr(_mod, "degree_centrality")


# ========================================================================== #
# Graph structure tests
# ========================================================================== #

def test_graph_basic_properties():
    """Undirected graph tracks num_nodes and num_edges correctly."""
    g = Graph(directed=False)
    g.add_node("a")
    g.add_node("b")
    g.add_node("c")
    assert g.num_nodes == 3
    assert g.num_edges == 0

    g.add_edge("a", "b", weight=2.0)
    g.add_edge("b", "c", weight=3.0)
    assert g.num_nodes == 3
    assert g.num_edges == 2  # each undirected edge counted once

    # Adding a duplicate edge must not increase the count
    g.add_edge("a", "b", weight=5.0)
    assert g.num_edges == 2


def test_graph_directed_basic():
    """Directed graph: add_edge does not create a reverse edge."""
    g = Graph(directed=True)
    g.add_edge("x", "y")
    g.add_edge("y", "z")
    assert g.num_nodes == 3
    assert g.num_edges == 2

    # No reverse edge: neighbors of y contains z but not x
    nbrs = dict(g.neighbors("y"))
    assert "z" in nbrs
    assert "x" not in nbrs


# ========================================================================== #
# BFS tests
# ========================================================================== #

def test_bfs_hop_distances():
    """BFS returns exact integer hop distances on a simple directed chain."""
    g = Graph(directed=True)
    #  0 -> 1 -> 2 -> 3
    #       |
    #       v
    #       4
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(1, 4)

    dist = bfs(g, 0)
    assert dist[0] == 0
    assert dist[1] == 1
    assert dist[2] == 2
    assert dist[3] == 3
    assert dist[4] == 2


def test_bfs_source_zero():
    """Source node always maps to hop distance 0."""
    g = Graph()
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    dist = bfs(g, "b")
    assert dist["b"] == 0


def test_bfs_disconnected():
    """BFS omits unreachable nodes."""
    g = Graph(directed=True)
    g.add_edge(1, 2)
    g.add_edge(3, 4)   # separate component

    dist = bfs(g, 1)
    assert 1 in dist
    assert 2 in dist
    assert 3 not in dist
    assert 4 not in dist


# ========================================================================== #
# Dijkstra tests
# ========================================================================== #

def test_dijkstra_weighted_path():
    """Key test: shortest WEIGHTED path differs from fewest hops.

    Graph:
        A --1.0--> B --1.0--> C
        A ---5.0-----------> C

    Fewest hops from A to C = 1 (direct edge, cost 5.0).
    Shortest weighted from A to C = A->B->C cost 2.0.

    The broken variant uses hop count and returns 1.0 for C (wrong).
    """
    g = Graph(directed=True)
    g.add_edge("A", "B", weight=1.0)
    g.add_edge("B", "C", weight=1.0)
    g.add_edge("A", "C", weight=5.0)

    dist = dijkstra(g, "A")
    assert dist["A"] == 0.0
    assert gu.close(dist["B"], 1.0)
    # Must be 2.0 (via B), NOT 5.0 (direct) and NOT 1.0 (hop count)
    assert gu.close(dist["C"], 2.0), (
        f"Expected 2.0 (via B), got {dist['C']}. "
        "Dijkstra must respect edge weights."
    )


def test_dijkstra_source_zero():
    """Source node maps to 0.0 in Dijkstra output."""
    g = Graph()
    g.add_edge(10, 20, weight=7.5)
    dist = dijkstra(g, 10)
    assert dist[10] == 0.0
    assert gu.close(dist[20], 7.5)


def test_dijkstra_single_node():
    """Single-node graph: Dijkstra returns {source: 0.0}."""
    g = Graph()
    g.add_node(42)
    dist = dijkstra(g, 42)
    assert dist == {42: 0.0}


# ========================================================================== #
# Connected components tests
# ========================================================================== #

def test_connected_components_two():
    """Undirected graph with two components returns exactly two sets."""
    g = Graph(directed=False)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_node(4)   # isolated
    g.add_node(5)   # isolated

    comps = connected_components(g)
    assert len(comps) == 3  # {1,2,3}, {4}, {5}

    sets = [frozenset(c) for c in comps]
    assert frozenset({1, 2, 3}) in sets
    assert frozenset({4}) in sets
    assert frozenset({5}) in sets


def test_connected_components_single():
    """Fully connected undirected graph has exactly one component."""
    g = Graph(directed=False)
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    g.add_edge("c", "a")

    comps = connected_components(g)
    assert len(comps) == 1
    assert frozenset(comps[0]) == frozenset({"a", "b", "c"})


# ========================================================================== #
# PageRank tests
# ========================================================================== #

def _build_nx_graph(our_graph: object, directed: bool) -> nx.DiGraph | nx.Graph:
    """Convert our Graph to a networkx graph for cross-checking."""
    if directed:
        nxg = nx.DiGraph()
    else:
        nxg = nx.Graph()
    nodes = list(our_graph.nodes())
    nxg.add_nodes_from(nodes)
    for u, v, w in our_graph.edges():
        nxg.add_edge(u, v, weight=w)
    return nxg


def test_pagerank_sums_to_one():
    """PageRank values must sum to approximately 1.0 (within 1e-6)."""
    g = Graph(directed=True)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 0)
    g.add_edge(0, 2)
    g.add_edge(3, 0)   # node 3 points into the cycle

    pr = pagerank(g, damping=0.85)
    total = sum(pr.values())
    assert abs(total - 1.0) < 1e-6, f"PageRank sum = {total}, expected ~1.0"
    # All nodes must appear in the result
    assert set(pr.keys()) == {0, 1, 2, 3}


def test_pagerank_vs_networkx():
    """Cross-check our pagerank against networkx.pagerank within tol 1e-3."""
    # Build a non-trivial directed graph
    g = Graph(directed=True)
    edges = [
        (0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0),
        (0, 2, 1.0), (1, 3, 1.0), (4, 0, 1.0), (4, 2, 1.0),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, weight=w)

    our_pr = pagerank(g, damping=0.85, max_iter=200, tol=1e-9)
    our_total = sum(our_pr.values())

    # Build the equivalent networkx graph
    nxg = nx.DiGraph()
    for u, v, w in edges:
        nxg.add_edge(u, v, weight=w)
    nx_pr = nx.pagerank(nxg, alpha=0.85, max_iter=200, tol=1e-9, weight=None)

    # Sums to ~1
    assert abs(our_total - 1.0) < 1e-6

    # Each node's rank is within 1e-3 of networkx
    for node in nxg.nodes():
        assert abs(our_pr[node] - nx_pr[node]) < 1e-3, (
            f"node {node}: ours={our_pr[node]:.6f}, nx={nx_pr[node]:.6f}"
        )


# ========================================================================== #
# Degree centrality tests
# ========================================================================== #

def test_degree_centrality_values():
    """Star graph: center has centrality 1.0; leaves have 1/(N-1)."""
    # Star: center -> leaf1, leaf2, leaf3, leaf4 (undirected)
    g = Graph(directed=False)
    g.add_edge("center", "leaf1")
    g.add_edge("center", "leaf2")
    g.add_edge("center", "leaf3")
    g.add_edge("center", "leaf4")
    # 5 nodes total; N-1 = 4
    dc = degree_centrality(g)

    assert gu.close(dc["center"], 1.0)        # 4 / 4
    assert gu.close(dc["leaf1"], 0.25)        # 1 / 4
    assert gu.close(dc["leaf2"], 0.25)
    assert gu.close(dc["leaf3"], 0.25)
    assert gu.close(dc["leaf4"], 0.25)


def test_degree_centrality_directed():
    """Directed graph uses total degree (in + out)."""
    g = Graph(directed=True)
    # A -> B, A -> C, D -> A
    # A: out=2, in=1, total=3; B: out=0, in=1, total=1; C: out=0, in=1, total=1
    # D: out=1, in=0, total=1; N=4, N-1=3
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("D", "A")

    dc = degree_centrality(g)
    assert gu.close(dc["A"], 3.0 / 3.0)  # 1.0
    assert gu.close(dc["B"], 1.0 / 3.0)
    assert gu.close(dc["C"], 1.0 / 3.0)
    assert gu.close(dc["D"], 1.0 / 3.0)


# ========================================================================== #
# Advisory code quality
# ========================================================================== #

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
