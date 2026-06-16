"""Generate the oracle-grounded mutation corpus for competitive/cp04_tree_distance.

Independent oracle: all-pairs Dijkstra — for each source node run Dijkstra over the
tree, return [sum_of_distances_from_i for i in range(n)]. O(n^2 log n) — structurally
independent of the gold's O(n) two-pass rerooting DP.

Provenance: Sum of distances in a tree (rerooting DP) — cf. LeetCode 834;
Codeforces rerooting tutorials. Grader ground truth: independent all-pairs
BFS/Dijkstra.

Run:  python3 experiment_mihaco/mutation_gen/gen_cp04.py
"""
from __future__ import annotations

import heapq
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "competitive", "cp04_tree_distance"
GOLD_DIR = gu.GOLD_ROOT / CATEGORY / TASK_ID
GOLD_SRC = (GOLD_DIR / "solution.py").read_text()
gold = ms.load_callable_from_source(GOLD_SRC, "sum_of_distances")

# Load __broken reference (correct-but-slow O(n^2) Dijkstra)
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / (TASK_ID + "__broken")
BROKEN_SRC = (BROKEN_DIR / "solution.py").read_text()
broken = ms.load_callable_from_source(BROKEN_SRC, "sum_of_distances")


# --- Independent oracle: all-pairs Dijkstra --------------------------------- #
def oracle(n: int, edges: list) -> list:
    """O(n^2 log n) reference — structurally independent of rerooting DP."""
    if n == 1:
        return [0]
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    def dijkstra_sum(src: int) -> int:
        dist = [float("inf")] * n
        dist[src] = 0
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        return int(sum(x for x in dist if x != float("inf")))

    return [dijkstra_sum(i) for i in range(n)]


# --- Hand-written "common-mistake" wrong solutions -------------------------- #
_WRONG_SOURCES = {
    # Bug: rerooting forgets to subtract the child subtree contribution (uses wrong formula)
    "reroot_forget_subtraction": '''
def sum_of_distances(n, edges):
    if n == 1:
        return [0]
    from collections import deque
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    parent = [-1] * n
    parent_w = [0] * n
    order = []
    sub_size = [1] * n
    down = [0] * n
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                parent_w[v] = w
                stack.append(v)
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            w = parent_w[u]
            sub_size[p] += sub_size[u]
            down[p] += down[u] + sub_size[u] * w
    ans = [0] * n
    ans[0] = down[0]
    for u in order:
        for v, w in adj[u]:
            if v == parent[u]:
                continue
            # BUG: forgot to subtract sub_size[v]*w (only adds, doesn't subtract)
            ans[v] = ans[u] + (n - sub_size[v]) * w
    return ans
''',
    # Bug: uses node COUNT instead of weighted distance (ignores weights in rerooting)
    "node_count_not_weighted": '''
def sum_of_distances(n, edges):
    if n == 1:
        return [0]
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    parent = [-1] * n
    parent_w = [0] * n
    order = []
    sub_size = [1] * n
    down = [0] * n
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                parent_w[v] = w
                stack.append(v)
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            # BUG: uses 1 instead of actual weight w (counts hops not distances)
            sub_size[p] += sub_size[u]
            down[p] += down[u] + sub_size[u] * 1
    ans = [0] * n
    ans[0] = down[0]
    for u in order:
        for v, w in adj[u]:
            if v == parent[u]:
                continue
            # BUG: uses 1 instead of w
            ans[v] = ans[u] + (n - 2 * sub_size[v]) * 1
    return ans
''',
    # Bug: off-by-one in subtree size (initializes sub_size[root]=0 instead of 1)
    "off_by_one_subsize": '''
def sum_of_distances(n, edges):
    if n == 1:
        return [0]
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    parent = [-1] * n
    parent_w = [0] * n
    order = []
    sub_size = [0] * n  # BUG: initialized to 0 instead of 1
    down = [0] * n
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                parent_w[v] = w
                stack.append(v)
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            w = parent_w[u]
            sub_size[p] += sub_size[u]
            down[p] += down[u] + sub_size[u] * w
    ans = [0] * n
    ans[0] = down[0]
    for u in order:
        for v, w in adj[u]:
            if v == parent[u]:
                continue
            ans[v] = ans[u] + (n - 2 * sub_size[v]) * w
    return ans
''',
    # Bug: rerooting uses wrong sign — adds both terms instead of subtracting
    "wrong_sign_rerooting": '''
def sum_of_distances(n, edges):
    if n == 1:
        return [0]
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    parent = [-1] * n
    parent_w = [0] * n
    order = []
    sub_size = [1] * n
    down = [0] * n
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                parent_w[v] = w
                stack.append(v)
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            w = parent_w[u]
            sub_size[p] += sub_size[u]
            down[p] += down[u] + sub_size[u] * w
    ans = [0] * n
    ans[0] = down[0]
    for u in order:
        for v, w in adj[u]:
            if v == parent[u]:
                continue
            # BUG: both terms added instead of subtracting sub_size[v]*w
            ans[v] = ans[u] + (n - sub_size[v]) * w + sub_size[v] * w
    return ans
''',
}


def _wrong_fns():
    wrongs = [(name, ms.load_callable_from_source(src, "sum_of_distances"))
              for name, src in _WRONG_SOURCES.items()]
    # Add the __broken reference (correct-but-slow O(n^2); will be correct on small inputs
    # but we include it so the corpus framework tracks it)
    wrongs.append(("__broken", broken))
    # Generate AST mutants of the gold source
    for label, src in ms.generate_mutants(GOLD_SRC):
        try:
            wrongs.append((label, ms.load_callable_from_source(src, "sum_of_distances")))
        except Exception:
            continue
    return wrongs


def _build_random_tree(n: int, rng: random.Random, max_w: int = 10) -> list:
    """Build a random tree on n nodes; returns list of (u, v, w)."""
    edges = []
    for v in range(1, n):
        u = rng.randint(0, v - 1)
        w = rng.randint(1, max_w)
        edges.append((u, v, w))
    return edges


def _build_path(n: int, rng: random.Random, max_w: int = 10) -> list:
    """Build a path 0-1-2-...(n-1)."""
    return [(i, i + 1, rng.randint(1, max_w)) for i in range(n - 1)]


def _build_star(n: int, rng: random.Random, max_w: int = 10) -> list:
    """Build a star with center 0 and n-1 leaves."""
    return [(0, i, rng.randint(1, max_w)) for i in range(1, n)]


def _inputs():
    rng = random.Random(20260616)
    out = []

    # Edge cases
    out.append((1, []))
    out.append((2, [(0, 1, 1)]))
    out.append((2, [(0, 1, 7)]))
    out.append((3, [(0, 1, 1), (1, 2, 1)]))   # path unit weights
    out.append((3, [(0, 1, 1), (1, 2, 2)]))   # path non-uniform
    out.append((4, [(0, 1, 1), (0, 2, 1), (0, 3, 1)]))  # star n=4 unit
    out.append((4, [(0, 1, 2), (0, 2, 3), (0, 3, 5)]))  # star weighted

    # Explicit small stars and paths
    for n in range(1, 8):
        out.append((n, _build_star(n, rng) if n > 1 else []))
        out.append((n, _build_path(n, rng) if n > 1 else []))

    # Random trees with n in [1, 40]
    for _ in range(800):
        n = rng.randint(1, 40)
        edges = _build_random_tree(n, rng)
        out.append((n, edges))

    # A few slightly larger trees
    for n in [50, 60, 80, 100]:
        out.append((n, _build_random_tree(n, rng)))
        out.append((n, _build_path(n, rng)))
        out.append((n, _build_star(n, rng)))

    # Weight=1 uniformly (tests subtree-size logic most cleanly)
    for n in [5, 10, 15, 20]:
        edges = [(v, rng.randint(0, v - 1), 1) for v in range(1, n)]
        # Build differently — random tree but rewrite weights to 1
        tree_edges = _build_random_tree(n, rng, max_w=1)
        out.append((n, tree_edges))

    # Caterpillar (spine + leaves)
    for spine in [5, 10, 15]:
        n = spine * 2
        edges = [(i, i + 1, rng.randint(1, 5)) for i in range(spine - 1)]
        edges += [(i, spine + i, rng.randint(1, 5)) for i in range(spine)]
        out.append((n, edges))

    return out


def main() -> int:
    wrongs = _wrong_fns()
    print(f"Total wrong solutions: {len(wrongs)}")
    corpus = ms.build_corpus(gold, oracle, wrongs, _inputs(), max_keep=120)
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "brute-force",
        "provenance": (
            "Sum of distances in a tree (rerooting DP) — cf. LeetCode 834; "
            "Codeforces rerooting tutorials. Grader ground truth: independent all-pairs BFS/Dijkstra."
        ),
        "input_seed": 20260616,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
