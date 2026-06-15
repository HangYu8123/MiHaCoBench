"""Grader for algorithmic/a05_resolve_build_order. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test catalogue (≥8 required for algorithmic):
  1.  test_no_tasks              — n=0, no deps → empty list
  2.  test_empty_deps            — n=5, no deps → [0,1,2,3,4] (lex order)
  3.  test_simple_chain          — 0→1→2→3 → [0,1,2,3]
  4.  test_diamond               — diamond dependency (0→1,0→2,1→3,2→3)
  5.  test_lex_tie_break         — multiple valid orders, must pick lex-smallest
  6.  test_disconnected_tasks    — some tasks have no edges at all
  7.  test_cycle_raises          — cycle (0→1→2→0) must raise ValueError
  8.  test_self_loop_raises      — self-loop (0,0) must raise ValueError
  9.  test_all_deps_respected    — verify every returned order satisfies all edges
  10. test_single_node           — n=1, no deps → [0]
  11. test_duplicate_edges       — duplicate edges must not cause issues
  12. test_hard_time_gate        — n=200000, ~400000 edges, must complete in 5 s
  13. test_soft_complexity       — empirical curve fit (soft, only fails >2 tiers off)
  14. test_code_quality          — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a05_resolve_build_order"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
resolve_build_order = gu.load_callable(SOL, "solution.py", "resolve_build_order")

# Fixed seed for all random data — grader must be deterministic.
_RNG = random.Random(42)


# ---------------------------------------------------------------------------
# Helper: verify an ordering respects all dependency edges
# ---------------------------------------------------------------------------

def _check_order(n: int, deps: list[tuple[int, int]], order: list[int]) -> None:
    """Assert that `order` is a valid topological sort of (n, deps)."""
    assert isinstance(order, list), "return value must be a list"
    assert len(order) == n, f"order length {len(order)} != n={n}"
    assert set(order) == set(range(n)), "order must contain each task exactly once"
    pos = {task: idx for idx, task in enumerate(order)}
    for a, b in deps:
        if a == b:
            continue  # self-loops should have raised earlier; skip here
        assert pos[a] < pos[b], (
            f"dep ({a},{b}) violated: {a} appears at position {pos[a]}, "
            f"{b} appears at position {pos[b]}"
        )


# ---------------------------------------------------------------------------
# 1  n=0: empty graph
# ---------------------------------------------------------------------------

def test_no_tasks():
    result = resolve_build_order(0, [])
    assert result == []


# ---------------------------------------------------------------------------
# 2  No deps: must return [0, 1, 2, ..., n-1] (lex order)
# ---------------------------------------------------------------------------

def test_empty_deps():
    result = resolve_build_order(5, [])
    assert result == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# 3  Simple chain: 0 → 1 → 2 → 3
# ---------------------------------------------------------------------------

def test_simple_chain():
    deps = [(0, 1), (1, 2), (2, 3)]
    result = resolve_build_order(4, deps)
    assert result == [0, 1, 2, 3]
    _check_order(4, deps, result)


# ---------------------------------------------------------------------------
# 4  Diamond: 0→1, 0→2, 1→3, 2→3
#    Lex-smallest: 0,1,2,3 (not 0,2,1,3)
# ---------------------------------------------------------------------------

def test_diamond():
    deps = [(0, 1), (0, 2), (1, 3), (2, 3)]
    result = resolve_build_order(4, deps)
    assert result == [0, 1, 2, 3], f"expected [0,1,2,3], got {result}"
    _check_order(4, deps, result)


# ---------------------------------------------------------------------------
# 5  Lex tie-break: two independent chains, lower indices must come first
#    Tasks: 0,1,2,3,4,5  Edges: 0→2, 1→3  (0 and 1 both free at start)
#    At start, ready = {0,1,4,5}. Lex: pick 0 first, then 1, then 2 and 3 open...
#    Expected: [0, 1, 2, 3, 4, 5]
# ---------------------------------------------------------------------------

def test_lex_tie_break():
    # Two chains: 0→2→4, 1→3→5
    deps = [(0, 2), (2, 4), (1, 3), (3, 5)]
    result = resolve_build_order(6, deps)
    # At every step, lex-smallest ready task must be chosen.
    # Ready at start: {0, 1}. Pick 0 → ready adds 2. Now {1, 2}. Pick 1 → adds 3.
    # Now {2, 3}. Pick 2 → adds 4. Now {3, 4}. Pick 3 → adds 5. Now {4, 5}. Pick 4,5.
    assert result == [0, 1, 2, 3, 4, 5], f"expected [0,1,2,3,4,5], got {result}"
    _check_order(6, deps, result)


# ---------------------------------------------------------------------------
# 6  Disconnected: some tasks have no edges (they sort by index among the free)
# ---------------------------------------------------------------------------

def test_disconnected_tasks():
    # n=6, only tasks 0→3 are connected; 4 and 5 are free from the start.
    # Initial heap: {0, 1, 2, 4, 5} (task 3 has in-degree 3).
    # Pop 0 → in_degree[3] = 2; heap {1,2,4,5}
    # Pop 1 → in_degree[3] = 1; heap {2,4,5}
    # Pop 2 → in_degree[3] = 0, push 3; heap {3,4,5}
    # Pop 3; heap {4,5}
    # Pop 4; Pop 5
    # Expected lex-smallest: [0, 1, 2, 3, 4, 5]
    deps = [(0, 3), (1, 3), (2, 3)]
    result = resolve_build_order(6, deps)
    _check_order(6, deps, result)
    assert result == [0, 1, 2, 3, 4, 5], f"got {result}"


# ---------------------------------------------------------------------------
# 7  Cycle: must raise ValueError
# ---------------------------------------------------------------------------

def test_cycle_raises():
    deps = [(0, 1), (1, 2), (2, 0)]
    with pytest.raises(ValueError):
        resolve_build_order(3, deps)


# ---------------------------------------------------------------------------
# 8  Self-loop: must raise ValueError
# ---------------------------------------------------------------------------

def test_self_loop_raises():
    deps = [(0, 0)]
    with pytest.raises(ValueError):
        resolve_build_order(3, deps)


# ---------------------------------------------------------------------------
# 9  General validity check across a moderately-large random DAG
# ---------------------------------------------------------------------------

def test_all_deps_respected():
    """Build a random DAG (no cycles), verify returned order respects all edges."""
    n = 50
    # Generate a DAG: only add edge (i, j) if i < j (guaranteed acyclic)
    rng = random.Random(17)
    deps = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < 0.15:
                deps.append((i, j))
    result = resolve_build_order(n, deps)
    _check_order(n, deps, result)


# ---------------------------------------------------------------------------
# 10  Single node
# ---------------------------------------------------------------------------

def test_single_node():
    result = resolve_build_order(1, [])
    assert result == [0]


# ---------------------------------------------------------------------------
# 11  Duplicate edges must not cause errors or wrong counts
# ---------------------------------------------------------------------------

def test_duplicate_edges():
    deps = [(0, 1), (0, 1), (1, 2), (1, 2), (0, 2)]
    result = resolve_build_order(3, deps)
    assert result == [0, 1, 2]
    _check_order(3, deps, result)


# ---------------------------------------------------------------------------
# 12  HARD time gate: n=200000, ~400000 random DAG edges, must finish in 5 s.
#     An O(V*E) repeated-scan solution (~200000 * 400000 = 8e10 ops) times out.
# ---------------------------------------------------------------------------

def test_hard_time_gate():
    """Large DAG: O(V+E) must complete in 5 s; O(V*E) would take far too long."""
    n = 200_000
    rng = random.Random(99)
    # Build a random DAG: only add edges (i, j) with i < j to guarantee no cycles.
    # Target ~400000 edges: each node i randomly picks ~2 successors from [i+1, n).
    deps: list[tuple[int, int]] = []
    for i in range(n - 1):
        # Each node adds 0-4 forward edges with low probability to hit ~400k total.
        k = rng.randint(0, 4)
        for _ in range(k):
            j = rng.randint(i + 1, n - 1)
            deps.append((i, j))
        if len(deps) >= 400_000:
            break

    result = gu.run_within(5.0, resolve_build_order, n, deps)

    # Verify the result is a valid permutation (spot-check; full dep check is O(E))
    assert isinstance(result, list)
    assert len(result) == n
    assert set(result) == set(range(n))
    # Spot-check: verify a sample of edges is respected
    pos = {task: idx for idx, task in enumerate(result)}
    sample = rng.sample(deps, min(1000, len(deps)))
    for a, b in sample:
        assert pos[a] < pos[b], f"dep ({a},{b}) violated in large-input test"


# ---------------------------------------------------------------------------
# 13  SOFT complexity signal (only fails if >2 tiers worse than O(n))
# ---------------------------------------------------------------------------

def test_soft_complexity():
    """Empirical time-complexity estimate — advisory; fails only if egregiously wrong."""
    sizes = [500, 1000, 2000, 5000, 10000, 20000]

    def make_input(n):
        rng = random.Random(n)
        deps = []
        for i in range(n - 1):
            if rng.random() < 0.4:
                j = rng.randint(i + 1, n - 1)
                deps.append((i, j))
        return (n, deps)

    timings = gu.measure_runtime(
        make_input,
        lambda pair: resolve_build_order(*pair),
        sizes,
        repeats=3,
    )
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n)  ranked={report['ranked'][:3]}")
    # Allow up to 2 tiers above O(n): O(n log n) and O(n^2) are the next two tiers.
    # Only fail for O(n^3) or worse (within_one_tier already handles 1-tier slack;
    # we call it twice to allow 2-tier slack).
    target = "O(n log n)"  # one tier above O(n) — within_one_tier gives +1 more
    assert gu.within_one_tier(label, target), (
        f"soft complexity check: estimated {label} is more than two tiers above O(n). "
        "This strongly indicates an O(V*E) or worse algorithm."
    )


# ---------------------------------------------------------------------------
# 14  Advisory code-quality report (never asserted)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
