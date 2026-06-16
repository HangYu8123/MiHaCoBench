"""Grader for debug/dbg02_resolve_order. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold (fixed) reference, FAILS on the broken
(still-buggy) reference. FAIL_TO_PASS tests assert a ValueError on cyclic inputs
(self-loop and direct/longer cycles); PASS_TO_PASS tests assert a valid load
order on acyclic graphs. Exceptions are asserted by TYPE, never by message.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg02_resolve_order"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
resolve_load_order = gu.load_callable(SOL, "solution.py", "resolve_load_order")


def _is_valid_order(order, deps):
    """Every dependency must appear before the module that requires it, and the
    order must be a permutation of the keys."""
    if sorted(order) != sorted(deps):
        return False
    pos = {name: i for i, name in enumerate(order)}
    return all(pos[dep] < pos[node] for node, ds in deps.items() for dep in ds)


# ---- FAIL_TO_PASS: cycle detection the bug omits ---------------------------- #
def test_self_dependency_raises():
    with pytest.raises(ValueError):
        resolve_load_order({"a": ["a"]})


def test_direct_two_node_cycle_raises():
    with pytest.raises(ValueError):
        resolve_load_order({"a": ["b"], "b": ["a"]})


def test_longer_cycle_raises():
    with pytest.raises(ValueError):
        resolve_load_order({"a": ["b"], "b": ["c"], "c": ["a"]})


# ---- PASS_TO_PASS: valid DAGs the buggy code already handles ----------------- #
def test_linear_chain_order():
    deps = {"a": ["b"], "b": ["c"], "c": []}
    order = resolve_load_order(deps)
    assert _is_valid_order(order, deps)
    assert order.index("c") < order.index("b") < order.index("a")


def test_diamond_dependency_order():
    deps = {"app": ["left", "right"], "left": ["base"], "right": ["base"], "base": []}
    order = resolve_load_order(deps)
    assert _is_valid_order(order, deps)


def test_single_node_and_empty():
    assert resolve_load_order({"only": []}) == ["only"]
    assert resolve_load_order({}) == []


def test_all_nodes_present_no_duplicates():
    deps = {"a": ["b", "c"], "b": ["c"], "c": [], "d": ["a"]}
    order = resolve_load_order(deps)
    assert sorted(order) == ["a", "b", "c", "d"]
    assert _is_valid_order(order, deps)


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
