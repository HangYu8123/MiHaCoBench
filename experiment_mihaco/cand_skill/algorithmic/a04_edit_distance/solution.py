def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.

    Uses a space-optimised single-row rolling DP array of size min(m, n) + 1.
    Empty-string inputs are handled naturally by the DP initialisation:
      - edit_distance("", s) == len(s)  (all insertions)
      - edit_distance(s, "") == len(s)  (all deletions)
      - edit_distance("", "")  == 0
    """
    # Ensure b is the shorter string so the rolling array stays as small as
    # possible (O(min(m, n)) space).
    if len(a) < len(b):
        a, b = b, a

    # prev_row[j] represents d[0][j] = j (base case: i=0 row).
    prev_row = list(range(len(b) + 1))

    for ca in a:
        # diag holds the value that was at prev_row[0] before this row starts,
        # i.e. the "upper-left" cell for column j=0.
        diag = prev_row[0]
        # d[i][0] = i  (cost of deleting all of a[:i])
        prev_row[0] += 1

        for j in range(1, len(b) + 1):
            # Save prev_row[j] (the cell directly above: d[i-1][j]) BEFORE
            # overwriting it; it becomes the diagonal for the next column.
            old_diag = diag
            diag = prev_row[j]

            cost = 0 if ca == b[j - 1] else 1
            prev_row[j] = min(
                prev_row[j] + 1,       # deletion:     d[i-1][j] + 1
                prev_row[j - 1] + 1,   # insertion:    d[i][j-1] + 1
                old_diag + cost,       # substitution: d[i-1][j-1] + cost
            )

    return prev_row[len(b)]
