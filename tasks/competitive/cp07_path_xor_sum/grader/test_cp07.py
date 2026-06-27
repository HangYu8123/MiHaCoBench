"""Grader for competitive/cp07_path_xor_sum. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Ground truth is an INDEPENDENT O(n^2) all-pairs BFS brute force (``_brute``): from
every source it BFS-accumulates the path-XOR to all other nodes and sums over
pairs. This does not use the gold's root-prefix / per-bit-counting identity, so it
is a genuinely separate oracle. It is used on SMALL trees only.

The broken reference miscounts each bit's pairs as the WITHIN-group count
(C(set,2)+C(unset,2)) instead of the CROSS product set*unset; it is fast (passes
the time gate) but wrong on essentially every non-degenerate input, so the
correctness tests are the discriminator.

Test catalogue (>=10 required for competitive):
  1.  test_singleton                  — n=1 -> 0
  2.  test_two_nodes                  — n=2 -> w (and zero-weight -> 0)
  3.  test_all_zero_weights           — every edge 0 -> 0
  4.  test_path_graph_known           — spelled-out path, vs brute
  5.  test_star_graph_known           — spelled-out star, vs brute
  6.  test_random_small_vs_brute      — many random trees vs brute
  7.  test_adversarial_structures     — path/star/balanced/random, large weights, vs brute
  8.  test_modulus_applied            — raw sum exceeds the modulus; result is reduced
  9.  test_time_gate                  — n=200000, fixed seed, timeout 5s (the real gate)
  10. test_soft_complexity            — empirical curve fit (soft, advisory)
  11. test_code_quality               — advisory only (never asserted)
"""
from __future__ import annotations

import random
from collections import deque

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "competitive", "cp07_path_xor_sum"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
sum_path_xor = gu.load_callable(SOL, "solution.py", "sum_path_xor")

MOD = 1_000_000_007


# ---------------------------------------------------------------------------
# Independent reference: O(n^2) all-pairs BFS. For SMALL n only.
# ---------------------------------------------------------------------------

def _brute(n: int, edges: list[tuple[int, int, int]]) -> int:
    if n <= 1:
        return 0
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    total = 0
    for s in range(n):
        dist = [None] * n
        dist[s] = 0
        dq = deque([s])
        while dq:
            u = dq.popleft()
            du = dist[u]
            for v, w in adj[u]:
                if dist[v] is None:
                    dist[v] = du ^ w
                    dq.append(v)
        for t in range(s + 1, n):
            total += dist[t]
    return total % MOD


def _random_tree(n: int, rng: random.Random, maxw: int = 1 << 30) -> list[tuple[int, int, int]]:
    """Random labelled tree: node v (>=1) attaches to a uniform earlier node."""
    edges = []
    for v in range(1, n):
        u = rng.randint(0, v - 1)
        w = rng.randint(0, maxw - 1)
        edges.append((u, v, w))
    return edges


# ---------------------------------------------------------------------------
# 1. Singleton — no pairs.
# ---------------------------------------------------------------------------

def test_singleton():
    assert sum_path_xor(1, []) == 0


# ---------------------------------------------------------------------------
# 2. Two nodes — the single edge weight (and a zero-weight variant).
# ---------------------------------------------------------------------------

def test_two_nodes():
    assert sum_path_xor(2, [(0, 1, 7)]) == 7
    assert sum_path_xor(2, [(0, 1, 0)]) == 0
    big = (1 << 29) + 12345
    assert sum_path_xor(2, [(0, 1, big)]) == big % MOD


# ---------------------------------------------------------------------------
# 3. All-zero weights — every path XOR is 0.
# ---------------------------------------------------------------------------

def test_all_zero_weights():
    edges = [(i, i + 1, 0) for i in range(9)]  # a 10-node path, all zero
    assert sum_path_xor(10, edges) == 0


# ---------------------------------------------------------------------------
# 4. Path graph — fully spelled out, checked against brute.
#    0 -1- 1 -2- 2 -4- 3  (weights 1,2,4)
#    pairs: (0,1)=1 (1,2)=2 (2,3)=4 (0,2)=1^2=3 (1,3)=2^4=6 (0,3)=1^2^4=7
#    sum = 1+2+4+3+6+7 = 23
# ---------------------------------------------------------------------------

def test_path_graph_known():
    edges = [(0, 1, 1), (1, 2, 2), (2, 3, 4)]
    assert sum_path_xor(4, edges) == 23
    assert sum_path_xor(4, edges) == _brute(4, edges)


# ---------------------------------------------------------------------------
# 5. Star graph — center 0 joined to leaves with weights 1,2,3.
#    leaf-leaf path XOR = w_i ^ w_j ; center-leaf = w_i.
#    (0,1)=1 (0,2)=2 (0,3)=3 (1,2)=1^2=3 (1,3)=1^3=2 (2,3)=2^3=1 -> 1+2+3+3+2+1=12
# ---------------------------------------------------------------------------

def test_star_graph_known():
    edges = [(0, 1, 1), (0, 2, 2), (0, 3, 3)]
    assert sum_path_xor(4, edges) == 12
    assert sum_path_xor(4, edges) == _brute(4, edges)


# ---------------------------------------------------------------------------
# 6. Many random small trees vs the independent brute reference.
# ---------------------------------------------------------------------------

def test_random_small_vs_brute():
    rng = random.Random(2026)
    for _ in range(300):
        n = rng.randint(1, 25)
        edges = _random_tree(n, rng, maxw=64)
        assert sum_path_xor(n, edges) == _brute(n, edges), f"n={n} edges={edges}"


# ---------------------------------------------------------------------------
# 7. Adversarial structures + large weights (exercises the full 30-bit range).
# ---------------------------------------------------------------------------

def test_adversarial_structures():
    rng = random.Random(99)
    # Path-shaped (degenerate), large weights.
    for _ in range(20):
        n = rng.randint(2, 30)
        edges = [(i, i + 1, rng.randint(0, (1 << 30) - 1)) for i in range(n - 1)]
        assert sum_path_xor(n, edges) == _brute(n, edges)
    # Star-shaped, large weights.
    for _ in range(20):
        n = rng.randint(2, 30)
        edges = [(0, i, rng.randint(0, (1 << 30) - 1)) for i in range(1, n)]
        assert sum_path_xor(n, edges) == _brute(n, edges)
    # Random trees, full-range weights.
    for _ in range(60):
        n = rng.randint(2, 30)
        edges = _random_tree(n, rng, maxw=1 << 30)
        assert sum_path_xor(n, edges) == _brute(n, edges)


# ---------------------------------------------------------------------------
# 8. Modulus is applied to the final sum (raw sum far exceeds MOD).
# ---------------------------------------------------------------------------

def test_modulus_applied():
    # A 4-node path with maximal-ish equal weights so the raw sum > MOD.
    w = (1 << 30) - 1
    n = 60
    edges = [(i, i + 1, w if i % 2 == 0 else (w >> 1)) for i in range(n - 1)]
    got = sum_path_xor(n, edges)
    assert 0 <= got < MOD
    assert got == _brute(n, edges)


# ---------------------------------------------------------------------------
# 9. ADVERSARIAL hard time gate: n=200000, fixed seed, timeout 5s.
# ---------------------------------------------------------------------------

@pytest.mark.adversarial
def test_time_gate():
    """n=200000 tree (fixed seed) must return within 5s.

    The O(n log V) gold finishes well under a second; any explicit all-pairs
    O(n^2) enumeration (~2e10 pairs) cannot. A path-shaped tree also stresses
    recursive traversals (must be iterative).
    """
    n = 200_000
    rng = random.Random(42)
    # Path-shaped worst case for recursion + random full-range weights.
    edges = [(i, i + 1, rng.randint(0, (1 << 30) - 1)) for i in range(n - 1)]

    result = gu.run_within(5.0, sum_path_xor, n, edges)
    assert isinstance(result, int)
    assert 0 <= result < MOD

    # Spot-check the same construction on a small instance against brute.
    rng2 = random.Random(42)
    n_small = 50
    edges_small = [(i, i + 1, rng2.randint(0, (1 << 30) - 1)) for i in range(n_small - 1)]
    assert sum_path_xor(n_small, edges_small) == _brute(n_small, edges_small)


# ---------------------------------------------------------------------------
# 10. SOFT complexity signal (advisory; fails only if >2 tiers worse than O(n)).
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    sizes = [1000, 2000, 4000, 8000, 16000]

    def make_input(n: int):
        rng = random.Random(n)
        edges = _random_tree(n, rng, maxw=1 << 30)
        return (n, edges)

    timings = gu.measure_runtime(
        make_input,
        lambda args: sum_path_xor(args[0], args[1]),
        sizes,
        repeats=2,
    )
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log V)  ranked={report['ranked'][:3]}")
    assert gu.within_one_tier(label, "O(n^2)"), (
        f"soft complexity check: estimated {label} is more than one tier above O(n^2)."
    )


# ---------------------------------------------------------------------------
# 11. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
