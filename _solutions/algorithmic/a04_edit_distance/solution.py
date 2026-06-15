"""Gold reference for algorithmic/a04_edit_distance.

Levenshtein edit distance with:
  - Time complexity  O(m * n)
  - Space complexity O(min(m, n))  — single-row in-place DP.
"""
from __future__ import annotations


def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings *a* and *b*.

    Each insertion, deletion, or substitution costs 1.

    Uses a single-row in-place rolling DP so peak memory is O(min(m, n))
    and no new list is allocated inside the main loop.
    """
    # Ensure b is the shorter string so we allocate the smaller array.
    if len(a) < len(b):
        a, b = b, a

    m, n = len(a), len(b)

    # row[j] represents edit_distance(a[:i], b[:j]) for the current row i.
    # Initialise to edit_distance("", b[:j]) = j.
    row = list(range(n + 1))

    for i in range(1, m + 1):
        # diag holds the value from row[j-1] BEFORE the current row update,
        # i.e., edit_distance(a[:i-1], b[:j-1]).
        diag = i - 1       # = row[0] from previous iteration
        row[0] = i         # edit_distance(a[:i], "") = i
        for j in range(1, n + 1):
            temp = row[j]  # save row[j] (= prev diagonal for next j)
            if a[i - 1] == b[j - 1]:
                row[j] = diag          # characters match — free
            else:
                row[j] = 1 + min(
                    row[j],      # deletion  (row[j] still holds old value = prev row)
                    row[j - 1],  # insertion (already updated in this row)
                    diag,        # substitution
                )
            diag = temp
    return row[n]
