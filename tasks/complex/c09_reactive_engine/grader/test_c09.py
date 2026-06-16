"""Grader for complex/c09_reactive_engine. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference
(whose invalidation does not propagate transitively, so a cell two hops downstream
of a changed input keeps serving a stale cached value).

Per-behaviour tests give method-level partial credit (ClassEval style).
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c09_reactive_engine"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
_engine = gu.load_module(SOL, "engine.py")
Engine = _engine.Engine


def test_constant_get():
    e = Engine()
    e.set_value("x", 5)
    assert e.get("x") == 5


def test_simple_formula():
    e = Engine()
    e.set_value("a", 2)
    e.set_value("b", 3)
    e.set_formula("s", ["a", "b"], lambda x, y: x + y)
    assert e.get("s") == 5


def test_chained_formula():
    e = Engine()
    e.set_value("a", 1)
    e.set_formula("b", ["a"], lambda x: x + 10)
    e.set_formula("c", ["b"], lambda x: x * 2)
    assert e.get("c") == 22  # (1+10)*2


def test_direct_dependent_invalidation():
    # 1-hop invalidation works in BOTH gold and broken (PASS_TO_PASS).
    e = Engine()
    e.set_value("a", 1)
    e.set_formula("b", ["a"], lambda x: x + 10)
    assert e.get("b") == 11
    e.set_value("a", 5)
    assert e.get("b") == 15


def test_transitive_invalidation():
    # 2-hop invalidation: the FAIL_TO_PASS discriminator. Broken leaves `c` stale.
    e = Engine()
    e.set_value("a", 1)
    e.set_formula("b", ["a"], lambda x: x + 10)
    e.set_formula("c", ["b"], lambda x: x * 2)
    assert e.get("c") == 22
    e.set_value("a", 5)
    assert e.get("c") == 30  # (5+10)*2 — broken returns the stale 22


def test_deep_chain_transitive_invalidation():
    e = Engine()
    e.set_value("v", 0)
    e.set_formula("l1", ["v"], lambda x: x + 1)
    e.set_formula("l2", ["l1"], lambda x: x + 1)
    e.set_formula("l3", ["l2"], lambda x: x + 1)
    assert e.get("l3") == 3
    e.set_value("v", 10)
    assert e.get("l3") == 13


def test_memoization_recompute_count():
    e = Engine()
    e.set_value("a", 2)
    e.set_formula("b", ["a"], lambda x: x * x)
    assert e.get("b") == 4
    assert e.get("b") == 4
    assert e.recompute_count("b") == 1  # second get served from clean cache


def test_single_recompute_per_invalidation():
    e = Engine()
    e.set_value("a", 1)
    e.set_formula("b", ["a"], lambda x: x + 1)
    e.get("b")
    assert e.recompute_count("b") == 1
    e.get("b")
    assert e.recompute_count("b") == 1
    e.set_value("a", 2)
    e.get("b")
    assert e.recompute_count("b") == 2


def test_unknown_name_raises():
    e = Engine()
    with pytest.raises(KeyError):
        e.get("nope")
    with pytest.raises(KeyError):
        e.recompute_count("nope")


def test_direct_cycle_raises_and_engine_usable():
    e = Engine()
    e.set_value("a", 1)
    e.set_formula("b", ["a"], lambda x: x + 1)
    with pytest.raises(ValueError):
        e.set_formula("a", ["a"], lambda x: x)  # self-dependency
    # engine still usable
    assert e.get("b") == 2


def test_indirect_cycle_raises_and_rolls_back():
    e = Engine()
    e.set_value("x", 1)
    e.set_formula("a", ["x"], lambda v: v + 1)
    e.set_formula("b", ["a"], lambda v: v * 10)
    assert e.get("b") == 20
    with pytest.raises(ValueError):
        e.set_formula("a", ["b"], lambda v: v)  # a<-b<-a cycle
    # a's old definition (depends on x) is intact -> engine still consistent
    assert e.get("a") == 2
    assert e.get("b") == 20


def test_batch_diamond_transitive():
    # Diamond: a,e inputs; b=a+1, c=a+e, d=b+c. A batch update of inputs must
    # invalidate the whole transitive cone so reads reflect the new inputs.
    e = Engine()
    e.set_value("a", 1)
    e.set_value("e", 1)
    e.set_formula("b", ["a"], lambda x: x + 1)
    e.set_formula("c", ["a", "e"], lambda x, y: x + y)
    e.set_formula("d", ["b", "c"], lambda x, y: x + y)
    assert e.get("d") == (2) + (2)  # b=2, c=2 -> 4
    e.batch({"a": 10, "e": 5})
    assert e.get("d") == (11) + (15)  # b=11, c=15 -> 26


@pytest.mark.code_quality
def test_code_quality():
    print("code_quality:", gu.code_quality_report(SOL))
