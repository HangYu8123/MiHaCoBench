def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.
    """
    # Handle trivial cases
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Orient so the shorter string drives the rolling array (space = O(min(m,n)))
    if len(a) > len(b):
        a, b = b, a

    n = len(a)
    # Rolling array: row[j] = edit distance from a[:j] to b[:i] after processing row i
    row = list(range(n + 1))

    for i in range(len(b)):
        ch = b[i]
        diag = row[0]   # dp[i-1][0] before overwrite
        row[0] = i + 1  # base case: distance from a[:0]="" to b[:i+1] is i+1
        for j in range(1, n + 1):
            save = row[j]  # will become diag for next j
            if a[j - 1] == ch:
                row[j] = diag
            else:
                row[j] = 1 + min(diag, row[j], row[j - 1])
            diag = save

    return row[n]
