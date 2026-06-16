"""Grader for compositional/cb07_graph_spectral.

Tests the public contract only (see TASK.md), cross-checking the spectral
partition against an INDEPENDENT networkx reference (algebraic_connectivity and
number_connected_components).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference reads the Fiedler value/vector from the WRONG eigenvalue
index (the smallest, ~0, instead of the second-smallest). So for a connected
graph fiedler_value is ~0 and `connected` is False — the happy-path and
FAIL_TO_PASS tests fail, while the exception-contract and disconnected-graph
tests still pass.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb07_graph_spectral"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

spectral_partition = gu.load_callable(SOL, "solution.py", "spectral_partition")


# ---------------------------------------------------------------------------
# Independent networkx reference (does NOT reuse the solution's machinery).
# ---------------------------------------------------------------------------
def _nx_reference(edges, n):
    """Build the graph with networkx and return reference quantities."""
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u, v, w in edges:
        G.add_edge(u, v, weight=float(w))
    n_comp = nx.number_connected_components(G)
    ac = None
    if n_comp == 1 and n >= 2:
        ac = float(nx.algebraic_connectivity(G, weight="weight"))
    return G, n_comp, ac


# A connected weighted path graph 0-1-2-3-4.
PATH_EDGES = [(0, 1, 1.0), (1, 2, 2.0), (2, 3, 1.5), (3, 4, 0.5)]
PATH_N = 5

# A connected 2x2 mesh (cycle) 0-1, 0-2, 1-3, 2-3.
MESH_EDGES = [(0, 1, 1.0), (0, 2, 1.0), (1, 3, 1.0), (2, 3, 1.0)]
MESH_N = 4

# Two disjoint components: {0,1} and {2,3}.
DISCONNECTED_EDGES = [(0, 1, 1.0), (2, 3, 2.0)]
DISCONNECTED_N = 4


# ---------------------------------------------------------------------------
# Test 1: return type and required keys
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    result = spectral_partition(PATH_EDGES, PATH_N)
    required_keys = {"fiedler_value", "partition", "connected", "n_components"}
    assert isinstance(result, dict), "spectral_partition() must return a dict"
    missing = required_keys - set(result.keys())
    assert not missing, f"Missing keys in result: {missing}"
    extra = set(result.keys()) - required_keys
    assert not extra, f"Unexpected extra keys: {extra}"


# ---------------------------------------------------------------------------
# Test 2: field types and partition shape
# ---------------------------------------------------------------------------
def test_field_types_and_shape():
    result = spectral_partition(PATH_EDGES, PATH_N)
    assert isinstance(result["fiedler_value"], float), "fiedler_value must be a float"
    assert isinstance(result["connected"], bool), "connected must be a Python bool"
    assert isinstance(result["n_components"], int), "n_components must be a Python int"
    part = result["partition"]
    assert isinstance(part, list), "partition must be a list"
    assert len(part) == PATH_N, f"partition length must be n={PATH_N}, got {len(part)}"
    assert all(p in (0, 1) for p in part), "partition entries must be 0 or 1"


# ---------------------------------------------------------------------------
# Test 3: happy path — fiedler_value matches networkx algebraic_connectivity
# ---------------------------------------------------------------------------
def test_path_fiedler_matches_networkx():
    result = spectral_partition(PATH_EDGES, PATH_N)
    _, n_comp, ac = _nx_reference(PATH_EDGES, PATH_N)
    assert n_comp == 1  # sanity: this fixture is connected
    assert gu.close(result["fiedler_value"], ac, rtol=1e-3), (
        f"fiedler_value {result['fiedler_value']} != algebraic_connectivity {ac}"
    )


# ---------------------------------------------------------------------------
# Test 4: happy path — partition splits nodes into two non-empty groups
# ---------------------------------------------------------------------------
def test_path_partition_splits_two_groups():
    result = spectral_partition(PATH_EDGES, PATH_N)
    part = result["partition"]
    assert 0 in part and 1 in part, (
        f"partition must split into two non-empty groups, got {part}"
    )


# ---------------------------------------------------------------------------
# Test 5: happy path — connected True, n_components == 1
# ---------------------------------------------------------------------------
def test_path_connected_flags():
    result = spectral_partition(PATH_EDGES, PATH_N)
    assert result["connected"] is True, "connected path graph must report connected=True"
    assert result["n_components"] == 1, (
        f"connected graph must have n_components==1, got {result['n_components']}"
    )


# ---------------------------------------------------------------------------
# Test 6: mesh graph — fiedler_value matches networkx, connected, two groups
# ---------------------------------------------------------------------------
def test_mesh_fiedler_and_split():
    result = spectral_partition(MESH_EDGES, MESH_N)
    _, n_comp, ac = _nx_reference(MESH_EDGES, MESH_N)
    assert n_comp == 1
    assert gu.close(result["fiedler_value"], ac, rtol=1e-3), (
        f"mesh fiedler_value {result['fiedler_value']} != algebraic_connectivity {ac}"
    )
    assert result["connected"] is True
    assert result["n_components"] == 1
    part = result["partition"]
    assert 0 in part and 1 in part, f"mesh partition must split, got {part}"


# ---------------------------------------------------------------------------
# Test 7: disconnected graph — connected False, n_components == 2, fiedler ~ 0
# ---------------------------------------------------------------------------
def test_disconnected_graph():
    result = spectral_partition(DISCONNECTED_EDGES, DISCONNECTED_N)
    _, n_comp, _ = _nx_reference(DISCONNECTED_EDGES, DISCONNECTED_N)
    assert n_comp == 2  # sanity
    assert result["connected"] is False, "disconnected graph must report connected=False"
    assert result["n_components"] == 2, (
        f"two-component graph must have n_components==2, got {result['n_components']}"
    )
    assert gu.close(result["fiedler_value"], 0.0, rtol=1e-6, atol=1e-6), (
        f"disconnected fiedler_value should be ~0, got {result['fiedler_value']}"
    )


# ---------------------------------------------------------------------------
# Test 8: isolated node counts as its own component
# ---------------------------------------------------------------------------
def test_isolated_node_components():
    # path 0-1-2 plus isolated node 3 -> 2 components.
    edges = [(0, 1, 1.0), (1, 2, 1.0)]
    result = spectral_partition(edges, 4)
    _, n_comp, _ = _nx_reference(edges, 4)
    assert n_comp == 2
    assert result["n_components"] == 2, (
        f"graph with one isolated node must have n_components==2, got {result['n_components']}"
    )
    assert result["connected"] is False


# ---------------------------------------------------------------------------
# Test 9: FAIL_TO_PASS — connected fiedler is strictly positive AND connected True
# ---------------------------------------------------------------------------
def test_fail_to_pass_connected_fiedler_positive():
    result = spectral_partition(PATH_EDGES, PATH_N)
    _, _, ac = _nx_reference(PATH_EDGES, PATH_N)
    assert result["fiedler_value"] > 1e-6, (
        f"connected graph fiedler_value must be > 1e-6, got {result['fiedler_value']}"
    )
    assert gu.close(result["fiedler_value"], ac, rtol=1e-3), (
        f"fiedler_value {result['fiedler_value']} != algebraic_connectivity {ac}"
    )
    assert result["connected"] is True, (
        "connected graph must report connected=True"
    )


# ---------------------------------------------------------------------------
# Test 10: n < 1 raises ValueError
# ---------------------------------------------------------------------------
def test_n_less_than_one_raises():
    with pytest.raises(ValueError):
        spectral_partition([], 0)


# ---------------------------------------------------------------------------
# Test 11: out-of-range edge endpoint raises ValueError
# ---------------------------------------------------------------------------
def test_out_of_range_endpoint_raises():
    with pytest.raises(ValueError):
        spectral_partition([(0, 5, 1.0)], 3)


# ---------------------------------------------------------------------------
# Test 12: non-positive weight raises ValueError
# ---------------------------------------------------------------------------
def test_non_positive_weight_raises():
    with pytest.raises(ValueError):
        spectral_partition([(0, 1, 0.0)], 2)
    with pytest.raises(ValueError):
        spectral_partition([(0, 1, -2.0)], 2)


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
