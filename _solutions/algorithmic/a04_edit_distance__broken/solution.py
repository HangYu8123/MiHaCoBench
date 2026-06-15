"""Deliberately-broken reference for algorithmic/a04_edit_distance.

Planted defect: builds a full (m+1) x (n+1) DP table — O(m*n) space.
Values are CORRECT, but at input size 4000x4000 the table consumes
far more than 50 MB of peak heap, so the space-gate test MUST fail.

This demonstrates that the grader enforces the O(min(m,n)) space
requirement, not just correctness.
"""
from __future__ import annotations


def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings *a* and *b*.

    BUG: allocates a full (m+1) x (n+1) DP table — O(m*n) space.
    Correct distances are returned but peak memory far exceeds the 50 MB gate.
    """
    m, n = len(a), len(b)

    # Allocate full 2-D table — O(m * n) space (the planted defect).
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # deletion
                    dp[i][j - 1],      # insertion
                    dp[i - 1][j - 1],  # substitution
                )

    return dp[m][n]
