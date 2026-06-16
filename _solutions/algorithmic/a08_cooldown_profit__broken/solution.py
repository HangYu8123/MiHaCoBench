"""Deliberately-broken reference for algorithmic/a08_cooldown_profit.

Planted defect: a GREEDY that sorts jobs by profit descending and greedily picks
each job that is still compatible (cooldown-respecting and non-overlapping) with
everything already chosen. This runs fast (so it survives the feasibility gate),
but it is SUBOPTIMAL: a cluster of many small-profit jobs can beat one
big-profit job that blocks the whole cluster. The grader's adversarial
correctness test exposes this.

It imports and runs cleanly on every input — the defect is a wrong (greedy)
algorithm, not a crash.
"""
from __future__ import annotations


def max_profit(jobs: list[tuple], gap: int) -> int:
    """Return a (WRONG) profit via profit-descending greedy selection.

    Same public contract as the gold, but the greedy choice is not optimal.
    """
    if not jobs:
        return 0

    # Greedy: consider jobs from most profitable to least.
    ordered = sorted(jobs, key=lambda j: (-j[2], j[0], j[1]))

    chosen: list[tuple] = []  # list of (start, end) of accepted jobs
    total = 0
    for s, e, p in ordered:
        ok = True
        for cs, ce in chosen:
            # Two jobs are compatible iff one ends at least `gap` before the
            # other starts (cooldown both directions).
            if s >= ce + gap or cs >= e + gap:
                continue
            ok = False
            break
        if ok:
            chosen.append((s, e))
            total += p

    return total
