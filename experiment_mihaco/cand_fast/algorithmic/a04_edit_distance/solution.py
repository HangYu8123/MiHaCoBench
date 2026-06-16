def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.

    Uses a rolling two-row DP approach with O(min(m, n)) space.
    """
    # Ensure b is the shorter string so the 1D array has length min(m, n) + 1
    if len(a) < len(b):
        a, b = b, a

    m, n = len(a), len(b)

    # prev[j] = edit_distance(a[:0], b[:j]) = j (base case: empty prefix of a)
    prev = list(range(n + 1))
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        # Cost of deleting all i characters of a[:i] to match empty b
        curr[0] = i
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                # Characters match: no substitution cost, take diagonal
                curr[j] = prev[j - 1]
            else:
                # Min of: substitution (prev[j-1]+1), deletion (prev[j]+1), insertion (curr[j-1]+1)
                curr[j] = 1 + min(prev[j - 1], prev[j], curr[j - 1])
        # Swap rows for next iteration
        prev, curr = curr, prev

    return prev[n]
