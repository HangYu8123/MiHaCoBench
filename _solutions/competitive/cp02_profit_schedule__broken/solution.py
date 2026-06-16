"""BROKEN reference for competitive/cp02_profit_schedule.

Planted defect: uses a GREEDY heuristic — always pick the highest-profit
remaining job that fits — instead of the correct O(n log n) DP.

This greedy approach passes most small/simple tests but gives the wrong answer
on adversarial inputs where one high-profit job blocks several medium-profit
jobs whose combined profit is larger.

Example adversarial failure:
  jobs = [(0, 10, 15), (0, 5, 8), (5, 10, 8)]
  Greedy picks (0,10,15) -> profit=15 (blocks everything else)
  Optimal picks (0,5,8) + (5,10,8) = 16
"""
from __future__ import annotations


def max_profit(jobs: list[tuple[int, int, int]]) -> int:
    """BROKEN: greedy highest-profit-first heuristic (incorrect in general)."""
    if not jobs:
        return 0

    # Sort by profit descending (greedy choice — WRONG in general)
    candidates = sorted(jobs, key=lambda j: -j[2])

    selected: list[tuple[int, int, int]] = []
    total = 0

    for job in candidates:
        start, end, profit = job
        if profit <= 0:
            continue  # never beneficial
        # Check compatibility with all already-selected jobs
        compatible = True
        for s_start, s_end, _ in selected:
            # Conflict if intervals overlap: not (end <= s_start or s_end <= start)
            if not (end <= s_start or s_end <= start):
                compatible = False
                break
        if compatible:
            selected.append(job)
            total += profit

    return total
