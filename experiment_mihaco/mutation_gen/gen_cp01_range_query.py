"""Generate the oracle-grounded mutation corpus for competitive/cp01_range_query.

Independent oracle: a plain-list brute-force implementation that is structurally
different from the gold dual-Fenwick BIT. For ("add", l, r, v) it iterates
arr[i] += v for i in range(l, r+1); for ("sum", l, r) it appends sum(arr[l:r+1]).
This is a correct but O(n*q) implementation — it is used ONLY at corpus
generation time on small inputs (n <= 200, q <= 200), so correctness vs. the
gold can be verified without timing out.

Provenance: Range-update/range-sum Fenwick (BIT) two-tree trick —
cf. cp-algorithms.com Fenwick Tree §3 Range Update and Range Query.
Grader ground truth: independent brute-force array (not a library).

Run:  python3 experiment_mihaco/mutation_gen/gen_cp01_range_query.py
"""
from __future__ import annotations

import copy
import random
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "competitive", "cp01_range_query"
GOLD_DIR = gu.GOLD_ROOT / CATEGORY / TASK_ID
GOLD_SRC = (GOLD_DIR / "solution.py").read_text()
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / (TASK_ID + "__broken")
BROKEN_SRC = (BROKEN_DIR / "solution.py").read_text()

gold = ms.load_callable_from_source(GOLD_SRC, "process_queries")
broken = ms.load_callable_from_source(BROKEN_SRC, "process_queries")


# --- Independent brute-force oracle (structurally different from gold BIT) -- #
def oracle(n: int, ops: list) -> list:
    """Plain-list brute force: O(n*q). Only used on small corpus inputs."""
    arr = [0] * n
    out: list[int] = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            for i in range(l, r + 1):
                arr[i] += v
        else:
            _, l, r = op
            out.append(sum(arr[l : r + 1]))
    return out


# --- Hand-written "common-mistake" wrong solutions --------------------------- #
_WRONG_SOURCES = {
    # A point-update-only Fenwick tree — cannot handle range updates correctly.
    # For range add [l, r, v], it only updates index l (misses r+1 negation BIT).
    "point_update_only": '''
def process_queries(n, ops):
    """BUG: uses point-update BIT only — range-add is wrong."""
    bit = [0] * (n + 2)

    def update(i, delta):
        i += 1
        while i <= n:
            bit[i] += delta
            i += i & (-i)

    def prefix(i):
        i += 1
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s

    results = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            # BUG: only updates l, not r+1 with -v (treats as point update)
            update(l, v)
        else:
            _, l, r = op
            results.append(prefix(r) - (prefix(l - 1) if l > 0 else 0))
    return results
''',
    # Off-by-one in prefix sum: sums [l, r) instead of [l, r] (misses index r).
    "off_by_one_sum": '''
def process_queries(n, ops):
    """BUG: sum is over [l, r) instead of [l, r] — off-by-one on the right."""
    arr = [0] * n
    results = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            for i in range(l, r + 1):
                arr[i] += v
        else:
            _, l, r = op
            results.append(sum(arr[l:r]))   # BUG: r not r+1
    return results
''',
    # Ignores the second BIT tree (B2) — uses only B1, producing wrong sums.
    "ignore_b2": '''
def process_queries(n, ops):
    """BUG: only maintains B1 (difference BIT), forgets B2 — sums are wrong."""
    size = n + 1
    b1 = [0] * (size + 1)

    def _update(tree, i, delta):
        while i <= size:
            tree[i] += delta
            i += i & (-i)

    def _prefix(tree, i):
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    results = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            l1, r1 = l + 1, r + 1
            _update(b1, l1, v)
            _update(b1, r1 + 1, -v)
            # BUG: skips updating b2 entirely
        else:
            _, l, r = op
            i1 = r + 1
            # BUG: computes with only b1, missing the b2 correction term
            prefix_r = _prefix(b1, i1) * (r + 1)
            prefix_l = (_prefix(b1, l) * l) if l > 0 else 0
            results.append(prefix_r - prefix_l)
    return results
''',
    # Wrong range: add uses range(l, r) instead of range(l, r+1) — misses last.
    "add_off_by_one": '''
def process_queries(n, ops):
    """BUG: range add uses range(l, r) — misses index r."""
    arr = [0] * n
    results = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            for i in range(l, r):   # BUG: should be r+1
                arr[i] += v
        else:
            _, l, r = op
            results.append(sum(arr[l:r + 1]))
    return results
''',
}


class _Timeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _Timeout()


def _wrong_fns():
    # Pre-filter mutants that would infinite-loop using SIGALRM timeout.
    # BIT mutations can cause infinite loops in multiple ways depending on
    # which arithmetic node gets mutated (e.g., `l1 = l+1` → `l1 = l-1`
    # triggers `_update(b1, 0, v)` which loops forever since 0 & (-0) = 0).
    # We probe each mutant on several representative inputs covering edge
    # cases (l=0, l=r, full range) to catch all hang patterns.
    #
    # Also apply per-call SIGALRM timeout within build_corpus itself via a
    # wrapper, so any mutant that passes the probe but hangs on a corpus
    # input is caught and treated as a crash (wrong answer).
    _PROBES = [
        (5, [("add", 0, 4, 1), ("sum", 0, 4)]),
        (1, [("add", 0, 0, 7), ("sum", 0, 0)]),
        (3, [("add", 0, 2, 1), ("sum", 0, 2)]),
        (4, [("add", 1, 3, 2), ("sum", 1, 3)]),
    ]

    wrongs = [("broken", broken)]
    wrongs += [(name, ms.load_callable_from_source(src, "process_queries"))
               for name, src in _WRONG_SOURCES.items()]
    skipped = 0
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    try:
        for label, src in ms.generate_mutants(GOLD_SRC):
            try:
                fn = ms.load_callable_from_source(src, "process_queries")
            except Exception:
                skipped += 1
                continue
            # Probe with 1-second timeout per input using SIGALRM
            hung = False
            for probe in _PROBES:
                signal.alarm(1)
                try:
                    fn(*copy.deepcopy(probe))
                    signal.alarm(0)  # cancel alarm
                except _Timeout:
                    print(f"  [skip infinite-loop mutant] {label}")
                    skipped += 1
                    hung = True
                    break
                except Exception:
                    signal.alarm(0)  # other exceptions OK — wrong answer but not hanging
            if hung:
                continue
            wrongs.append((label, fn))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    if skipped:
        print(f"  Skipped {skipped} hanging/unloadable mutants")
    return wrongs


def _inputs():
    rng = random.Random(20260616)
    out = []

    # Edge cases first
    # Empty ops
    out.append((1, []))
    out.append((5, []))
    # n=1 with add and sum
    out.append((1, [("add", 0, 0, 7), ("sum", 0, 0)]))
    out.append((1, [("add", 0, 0, -3), ("sum", 0, 0)]))
    out.append((1, [("add", 0, 0, 1), ("add", 0, 0, 2), ("sum", 0, 0)]))
    # All add, no sum
    out.append((5, [("add", 0, 4, 1), ("add", 1, 3, 2)]))
    # l == r (point update + point sum)
    out.append((10, [("add", 5, 5, 100), ("sum", 5, 5)]))
    out.append((10, [("add", 0, 0, 42), ("sum", 0, 9)]))
    # Full range
    out.append((5, [("add", 0, 4, 3), ("sum", 0, 4)]))
    out.append((6, [("add", 0, 5, 7), ("sum", 0, 5)]))
    # Negative values
    out.append((5, [("add", 0, 4, 10), ("add", 1, 3, -15), ("sum", 0, 4), ("sum", 1, 3)]))
    # Sum before any add (should be 0)
    out.append((5, [("sum", 0, 4)]))
    out.append((3, [("sum", 0, 0), ("sum", 1, 1), ("sum", 2, 2)]))

    # Random small instances (n <= 20, q <= 20 for speed)
    # Keep inputs small so brute-force oracle finishes quickly on all wrongs.
    for _ in range(500):
        n = rng.randint(1, 20)
        q = rng.randint(0, 20)
        ops = []
        for _ in range(q):
            l = rng.randint(0, n - 1)
            r = rng.randint(l, n - 1)
            if rng.random() < 0.5:
                v = rng.randint(-1000, 1000)
                ops.append(("add", l, r, v))
            else:
                ops.append(("sum", l, r))
        out.append((n, ops))

    # Some instances with only sum ops (all zeros, result all 0)
    for _ in range(20):
        n = rng.randint(1, 15)
        q = rng.randint(1, 10)
        ops = [("sum", rng.randint(0, n - 1), n - 1) for _ in range(q)]
        out.append((n, ops))

    # Some instances with dense overlapping adds then sums (small n)
    for _ in range(50):
        n = rng.randint(5, 20)
        ops = []
        for _ in range(10):
            l = rng.randint(0, n - 1)
            r = rng.randint(l, n - 1)
            ops.append(("add", l, r, rng.randint(-500, 500)))
        for _ in range(10):
            l = rng.randint(0, n - 1)
            r = rng.randint(l, n - 1)
            ops.append(("sum", l, r))
        out.append((n, ops))

    return out


def main() -> int:
    import time
    t0 = time.time()
    print(f"[T+{time.time()-t0:.1f}] loading wrongs...")
    sys.stdout.flush()
    wrongs = _wrong_fns()
    print(f"[T+{time.time()-t0:.1f}] Total wrong solutions: {len(wrongs)}")
    sys.stdout.flush()
    inputs = _inputs()
    print(f"[T+{time.time()-t0:.1f}] Total inputs: {len(inputs)}")
    sys.stdout.flush()
    corpus = ms.build_corpus(gold, oracle, wrongs, inputs, max_keep=120)
    print(f"[T+{time.time()-t0:.1f}] corpus built")
    sys.stdout.flush()
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "brute-force",
        "provenance": (
            "Range-update/range-sum Fenwick (BIT) two-tree trick — "
            "cf. cp-algorithms.com Fenwick Tree §3 Range Update and Range Query. "
            "Grader ground truth: independent brute-force array (not a library)."
        ),
        "input_seed": 20260616,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
