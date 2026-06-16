"""Generate the oracle-grounded mutation corpus for competitive/cp02_profit_schedule.

Independent oracle: brute-force 2^n subset enumeration for n<=16.
For each subset, check that no two jobs overlap (next.start < prev.end means conflict).
Return the maximum total profit (>= 0, empty subset allowed).

This is structurally independent of the gold O(n log n) DP + binary search.

Provenance: Weighted interval scheduling / maximum-profit job scheduling —
cf. LeetCode 1235; CLRS ch.16. Grader ground truth: independent 2^n subset brute force.

Run:  python3 experiment_mihaco/mutation_gen/gen_cp02_profit_schedule.py
"""
from __future__ import annotations

import random
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "competitive", "cp02_profit_schedule"
GOLD_DIR = gu.GOLD_ROOT / CATEGORY / TASK_ID
GOLD_SRC = (GOLD_DIR / "solution.py").read_text()
gold = ms.load_callable_from_source(GOLD_SRC, "max_profit")

# Load __broken reference
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / f"{TASK_ID}__broken"
BROKEN_SRC = (BROKEN_DIR / "solution.py").read_text()
broken = ms.load_callable_from_source(BROKEN_SRC, "max_profit")


# --- Independent brute-force oracle: 2^n subset enumeration --------------- #
def oracle(jobs: list) -> int:
    """Enumerate all 2^n subsets; keep those with no overlapping pair; return max profit."""
    n = len(jobs)
    if n == 0:
        return 0
    assert n <= 16, f"oracle requires n<=16, got {n}"

    best = 0
    # Iterate over all non-empty subsets
    for r in range(1, n + 1):
        for subset in combinations(range(n), r):
            # Sort selected jobs by end time to check compatibility
            selected = sorted([jobs[i] for i in subset], key=lambda j: j[1])
            # Check pairwise compatibility: adjacent jobs in sorted order suffice
            valid = True
            for k in range(len(selected) - 1):
                # next.start < prev.end => conflict
                if selected[k + 1][0] < selected[k][1]:
                    valid = False
                    break
            if valid:
                total = sum(j[2] for j in selected)
                if total > best:
                    best = total
    return best


# --- Hand-written "common-mistake" wrong solutions ------------------------- #
_WRONG_SOURCES = {
    # Greedy by profit (the real __broken but re-written)
    "greedy_by_profit": '''
def max_profit(jobs):
    if not jobs:
        return 0
    candidates = sorted(jobs, key=lambda j: -j[2])
    selected = []
    total = 0
    for job in candidates:
        start, end, profit = job
        if profit <= 0:
            continue
        compatible = True
        for s_start, s_end, _ in selected:
            if not (end <= s_start or s_end <= start):
                compatible = False
                break
        if compatible:
            selected.append(job)
            total += profit
    return total
''',
    # Greedy by earliest end time
    "greedy_earliest_end": '''
def max_profit(jobs):
    if not jobs:
        return 0
    sorted_jobs = sorted(jobs, key=lambda j: j[1])
    total = 0
    last_end = float('-inf')
    for start, end, profit in sorted_jobs:
        if start >= last_end and profit > 0:
            total += profit
            last_end = end
    return total
''',
    # DP with wrong conflict rule: uses start < end (strict) instead of start >= end
    "dp_wrong_conflict_rule": '''
import bisect
def max_profit(jobs):
    if not jobs:
        return 0
    sorted_jobs = sorted(jobs, key=lambda j: (j[1], j[0]))
    n = len(sorted_jobs)
    ends = [j[1] for j in sorted_jobs]
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        start_i, end_i, profit_i = sorted_jobs[i - 1]
        # BUG: uses bisect_left instead of bisect_right, so adjacency (start==prev_end) is wrong
        p = bisect.bisect_left(ends, start_i, 0, i - 1)
        dp[i] = max(dp[i - 1], dp[p] + profit_i)
    return dp[n]
''',
    # DP that forgets to allow skipping negative-profit jobs (takes max with 0 each time)
    # Actually this is hard to get wrong in the DP formulation; let's use a version
    # that doesn't initialize dp[0]=0 but always takes the job
    "dp_no_skip": '''
import bisect
def max_profit(jobs):
    if not jobs:
        return 0
    sorted_jobs = sorted(jobs, key=lambda j: (j[1], j[0]))
    n = len(sorted_jobs)
    ends = [j[1] for j in sorted_jobs]
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        start_i, end_i, profit_i = sorted_jobs[i - 1]
        p = bisect.bisect_right(ends, start_i, 0, i - 1)
        # BUG: always adds profit even if negative (no max with dp[i-1] skip)
        dp[i] = dp[p] + profit_i
    return max(0, dp[n])
''',
}


def _wrong_fns():
    wrongs = []
    # Load __broken reference
    wrongs.append(("__broken", broken))
    # Hand-written wrong solutions
    for name, src in _WRONG_SOURCES.items():
        try:
            fn = ms.load_callable_from_source(src, "max_profit")
            wrongs.append((name, fn))
        except Exception as e:
            print(f"  warning: failed to load {name!r}: {e}")
    # AST mutants of the gold
    for label, src in ms.generate_mutants(GOLD_SRC):
        try:
            fn = ms.load_callable_from_source(src, "max_profit")
            wrongs.append((label, fn))
        except Exception:
            continue
    return wrongs


def _inputs():
    rng = random.Random(20260616)
    out = []

    # Random job lists with n in [0,14]
    for _ in range(3000):
        n = rng.randint(0, 14)
        jobs = []
        for _ in range(n):
            start = rng.randint(0, 20)
            end = start + rng.randint(1, 10)
            profit = rng.randint(-5, 20)
            jobs.append((start, end, profit))
        out.append((jobs,))

    # More inputs with n in [1, 16] to hit n=16 too
    for _ in range(500):
        n = rng.randint(1, 16)
        jobs = []
        for _ in range(n):
            start = rng.randint(0, 15)
            end = start + rng.randint(1, 8)
            profit = rng.randint(-5, 20)
            jobs.append((start, end, profit))
        out.append((jobs,))

    # Explicit edge cases
    # Empty
    out.append(([],))
    # Single job positive
    out.append(([(1, 5, 50)],))
    # Single job negative
    out.append(([(1, 5, -10)],))
    # Two overlapping
    out.append(([(1, 4, 30), (3, 6, 60)],))
    # Two disjoint
    out.append(([(1, 3, 30), (5, 8, 40)],))
    # Adjacency: end == start => compatible
    out.append(([(1, 5, 20), (5, 9, 30)],))
    # All negative
    out.append(([(-5, 0, -1), (0, 3, -100), (2, 7, -50)],))
    # All overlapping
    out.append(([(0, 10, 5), (0, 10, 20), (0, 10, 15)],))
    # Chain of three
    out.append(([(0, 2, 10), (2, 5, 15), (5, 8, 25)],))
    # Greedy adversarial: two medium beat one big
    out.append(([(0, 10, 15), (0, 5, 8), (5, 10, 8)],))
    # Greedy adversarial v2: three small beat one big
    out.append(([(0, 6, 20), (0, 2, 8), (2, 4, 8), (4, 6, 8)],))
    # All zero profit
    out.append(([(0, 3, 0), (3, 6, 0), (0, 6, 10)],))
    # Mixed with adjacency and negative
    out.append(([(0, 2, 5), (2, 4, -3), (4, 6, 7)],))
    # Dense overlapping region
    out.append(([(0, 5, 10), (1, 5, 12), (2, 5, 15), (3, 5, 8), (5, 8, 20)],))

    return out


def main() -> int:
    wrongs = _wrong_fns()
    print(f"Total wrong solutions: {len(wrongs)}")
    corpus = ms.build_corpus(gold, oracle, wrongs, _inputs(), max_keep=120)
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "brute-force",
        "provenance": "Weighted interval scheduling / maximum-profit job scheduling — cf. LeetCode 1235; CLRS ch.16. Grader ground truth: independent 2^n subset brute force.",
        "input_seed": 20260616,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
