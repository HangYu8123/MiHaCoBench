def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.

    Uses O(min(m, n)) space with a rolling single-row DP array.
    Time complexity: O(m * n).
    """
    # Ensure b is the shorter string to minimize space usage
    if len(a) < len(b):
        a, b = b, a

    m, n = len(a), len(b)

    # dp[j] represents edit_distance(a[:i], b[:j])
    # We only keep the current row and use a scalar for the diagonal
    dp = list(range(n + 1))

    for i in range(1, m + 1):
        prev = dp[0]  # This is dp[i-1][j-1] (diagonal)
        dp[0] = i     # edit_distance(a[:i], "") = i

        for j in range(1, n + 1):
            temp = dp[j]  # Save dp[i-1][j] before overwriting
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev,      # substitution
                                 dp[j],     # deletion (from a)
                                 dp[j - 1]) # insertion (into a)
            prev = temp

    return dp[n]
