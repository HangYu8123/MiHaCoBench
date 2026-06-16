"""Grader for compositional/cb02_workflow_dag.

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant skips cycle detection, so the cycle test fails (broken does
not raise ValueError for cyclic input). All acyclic tests pass on both variants.

Tests (>=6):
 1. test_layers_diamond        — correct layers on a diamond DAG
 2. test_order_valid           — returned order is a valid topological sort
 3. test_html_contains_layer   — html contains 'Layer'
 4. test_html_contains_names   — html contains every task name
 5. test_cycle_raises          — cycle input raises ValueError  ← broken fails here
 6. test_empty_workflow        — empty input returns empty layers/order + html
 7. test_linear_chain          — linear A->B->C->D produces 4 singleton layers
 8. test_source_uses           — yaml, networkx, jinja2 all appear in the source
 9. test_code_quality          — advisory only
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb02_workflow_dag"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

build_report = gu.load_callable(SOL, "solution.py", "build_report")

# ------------------------------------------------------------------ #
# Inline YAML fixtures (no committed data needed)
# ------------------------------------------------------------------ #

# Diamond DAG:  A -> B, A -> C, B -> D, C -> D
_DIAMOND_YAML = """\
tasks:
  - name: A
  - name: B
    deps: [A]
  - name: C
    deps: [A]
  - name: D
    deps: [B, C]
"""

# Linear chain: A -> B -> C -> D
_LINEAR_YAML = """\
tasks:
  - name: A
  - name: B
    deps: [A]
  - name: C
    deps: [B]
  - name: D
    deps: [C]
"""

# Cyclic: A -> B -> C -> A
_CYCLE_YAML = """\
tasks:
  - name: A
    deps: [C]
  - name: B
    deps: [A]
  - name: C
    deps: [B]
"""

# Empty
_EMPTY_YAML = "tasks: []"


# ------------------------------------------------------------------ #
# Layer correctness
# ------------------------------------------------------------------ #

def test_layers_diamond():
    """Diamond DAG must produce exactly 3 layers: [A], [B,C], [D]."""
    result = build_report(_DIAMOND_YAML)
    layers = result["layers"]
    assert isinstance(layers, list), "layers must be a list"
    assert len(layers) == 3, f"Expected 3 layers, got {len(layers)}: {layers}"
    assert layers[0] == ["A"], f"Layer 0 must be ['A'], got {layers[0]}"
    assert layers[1] == ["B", "C"], (
        f"Layer 1 must be ['B', 'C'] (sorted), got {layers[1]}"
    )
    assert layers[2] == ["D"], f"Layer 2 must be ['D'], got {layers[2]}"


def test_linear_chain():
    """Linear chain A->B->C->D must produce 4 singleton layers."""
    result = build_report(_LINEAR_YAML)
    layers = result["layers"]
    assert layers == [["A"], ["B"], ["C"], ["D"]], (
        f"Expected [['A'],['B'],['C'],['D']], got {layers}"
    )


# ------------------------------------------------------------------ #
# Topological order validity
# ------------------------------------------------------------------ #

def test_order_valid():
    """order must be a valid topological sort of the diamond DAG."""
    result = build_report(_DIAMOND_YAML)
    order = result["order"]
    assert isinstance(order, list), "order must be a list"
    assert set(order) == {"A", "B", "C", "D"}, (
        f"order must contain all tasks, got {order}"
    )
    pos = {name: i for i, name in enumerate(order)}
    # Edges: A->B, A->C, B->D, C->D
    for u, v in [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]:
        assert pos[u] < pos[v], (
            f"Dependency violation: {u} must come before {v} in order, got {order}"
        )


# ------------------------------------------------------------------ #
# HTML content
# ------------------------------------------------------------------ #

def test_html_contains_layer():
    """html must contain the substring 'Layer'."""
    result = build_report(_DIAMOND_YAML)
    html = result["html"]
    assert isinstance(html, str), "html must be a str"
    assert "Layer" in html, f"'Layer' not found in html: {html[:200]}"


def test_html_contains_names():
    """html must mention every task name at least once."""
    result = build_report(_DIAMOND_YAML)
    html = result["html"]
    for name in ("A", "B", "C", "D"):
        assert name in html, f"Task name '{name}' not found in html"


# ------------------------------------------------------------------ #
# Cycle detection  ← this test FAILS on the broken variant
# ------------------------------------------------------------------ #

def test_cycle_raises():
    """A cyclic workflow must raise ValueError."""
    with pytest.raises(ValueError):
        build_report(_CYCLE_YAML)


# ------------------------------------------------------------------ #
# Empty workflow
# ------------------------------------------------------------------ #

def test_empty_workflow():
    """Empty task list returns layers=[], order=[], html is a non-empty str."""
    result = build_report(_EMPTY_YAML)
    assert result["layers"] == [], f"Expected [], got {result['layers']}"
    assert result["order"] == [], f"Expected [], got {result['order']}"
    assert isinstance(result["html"], str) and len(result["html"]) > 0, (
        "html must be a non-empty string even for empty workflow"
    )


# ------------------------------------------------------------------ #
# Surface-form library constraint
# ------------------------------------------------------------------ #

def test_source_uses():
    """Solution must use yaml, networkx, and jinja2 in its source."""
    uses = gu.source_uses(SOL, ["networkx", "jinja2", "yaml"])
    for lib, present in uses.items():
        assert present, f"Required library '{lib}' not found in solution source"


# ------------------------------------------------------------------ #
# Advisory code quality
# ------------------------------------------------------------------ #

@pytest.mark.code_quality
def test_code_quality():
    """Advisory only — prints code quality metrics, never fails."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
