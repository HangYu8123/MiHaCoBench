def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.
    Uses O(min(m, n)) space with a single rolling row DP array.
    """
    # Ensure b is the shorter string to minimize space usage
    if len(a) < len(b):
        a, b = b, a

    m, n = len(a), len(b)

    # prev[j] represents edit_distance(a[:i], b[:j])
    # Initialize for i=0: edit_distance("", b[:j]) = j
    prev = list(range(n + 1))

    for i in range(1, m + 1):
        # curr[0] = edit_distance(a[:i], "") = i
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j - 1],  # substitution
                                   prev[j],       # deletion
                                   curr[j - 1])   # insertion
        prev = curr

    return prev[n]
