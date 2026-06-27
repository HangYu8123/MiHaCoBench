"""solution.py — Range Update / Range Sum via dual Fenwick BIT.

Public contract:
    process_queries(n, ops) -> list[int]

Each op is ("add", l, r, v) or ("sum", l, r), 0-indexed, per TASK.md.

Approach: dual BIT (B1, B2) with 1-based indexing.

Key identity (1-based BIT index i):
    prefix_sum(i) = B1.query(i) * i  -  B2.query(i)

For range_add on 0-based [l, r] with value v, translated to 1-based [l+1, r+1]:
    B1.add(l+1,  v)
    B1.add(r+2, -v)
    B2.add(l+1,  v * l)       # v * (l_1based - 1) = v * l
    B2.add(r+2, -v * (r+1))   # -v * r_1based      = -v * (r+1)

prefix_sum for 0-based index i:
    = B1.query(i+1) * (i+1) - B2.query(i+1)

range_sum for 0-based [l, r]:
    = prefix_sum(r) - prefix_sum(l-1)
    = prefix_sum(r) - prefix_sum(l-1)
    where prefix_sum(-1) == 0 (BIT.query(0) == 0 by loop guard)
"""


class _BIT:
    """1-based Fenwick tree supporting point add and prefix sum query."""

    __slots__ = ("_n", "_tree")

    def __init__(self, size: int) -> None:
        self._n = size
        self._tree = [0] * (size + 1)  # indices 0..size; index 0 unused

    def add(self, i: int, delta: int) -> None:
        """Add delta to position i (1-based)."""
        n = self._n
        tree = self._tree
        while i <= n:
            tree[i] += delta
            i += i & (-i)

    def query(self, i: int) -> int:
        """Return prefix sum [1..i] (1-based). Returns 0 for i <= 0."""
        s = 0
        tree = self._tree
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s


def process_queries(n: int, ops: list) -> list:
    """Process a sequence of range operations on an array of n zeros.

    Each element of ops is one of:
      ("add", l, r, v)  — add integer v to every index in [l, r] (0-indexed)
      ("sum", l, r)     — return the current sum of elements at [l, r]

    Return a list of integers: one result per "sum" operation, in order.
    """
    # BIT size: n+1 covers 1-based indices 1..n+1 (needed when r=n-1 → add at r+2=n+1)
    size = n + 1
    b1 = _BIT(size)
    b2 = _BIT(size)

    def _prefix(i_0based: int) -> int:
        """Prefix sum of 0-based array [0..i_0based]."""
        k = i_0based + 1  # convert to 1-based BIT index
        return b1.query(k) * k - b2.query(k)

    results = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            # 0-based [l, r] → 1-based [l+1, r+1]; sentinel at r+2
            l1 = l + 1
            r1 = r + 1
            b1.add(l1,     v)
            b1.add(r1 + 1, -v)
            b2.add(l1,     v * l)        # v * (l1 - 1)
            b2.add(r1 + 1, -v * r1)      # -v * r1
        else:  # "sum"
            _, l, r = op
            # range sum [l, r] = prefix(r) - prefix(l-1)
            # prefix(-1) = BIT.query(0) = 0 automatically
            total = _prefix(r) - (_prefix(l - 1) if l > 0 else 0)
            results.append(total)

    return results


# ---------------------------------------------------------------------------
# Self-test (TDD verification of contract examples)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example 1: basic interleaved adds and sums
    ops = [
        ("add", 0, 4, 1),   # [1, 1, 1, 1, 1]
        ("sum", 0, 4),       # 5
        ("add", 1, 3, 2),   # [1, 3, 3, 3, 1]
        ("sum", 1, 3),       # 9
        ("sum", 0, 0),       # 1
    ]
    result = process_queries(5, ops)
    assert result == [5, 9, 1], f"Example 1 failed: {result}"

    # Example 2: single element
    ops2 = [("add", 0, 0, 7), ("sum", 0, 0)]
    result2 = process_queries(1, ops2)
    assert result2 == [7], f"Example 2 failed: {result2}"

    # Example 3: no sum queries
    result3 = process_queries(3, [("add", 0, 2, 5)])
    assert result3 == [], f"Example 3 failed: {result3}"

    # Example 4: empty ops
    result4 = process_queries(10, [])
    assert result4 == [], f"Example 4 failed: {result4}"

    # Extra: negative v
    ops5 = [
        ("add", 0, 2, 10),
        ("add", 1, 2, -3),
        ("sum", 0, 2),   # arr = [10, 7, 7] → sum = 24
        ("sum", 1, 1),   # 7
    ]
    result5 = process_queries(3, ops5)
    assert result5 == [24, 7], f"Extra test failed: {result5}"

    # Extra: sum at boundary l=0 (tests prefix(-1)==0 path)
    ops6 = [("add", 0, 0, 42), ("sum", 0, 0)]
    result6 = process_queries(5, ops6)
    assert result6 == [42], f"Boundary test failed: {result6}"

    # Extra: large n sentinel boundary (r = n-1)
    n_big = 10
    ops7 = [("add", 0, n_big - 1, 1), ("sum", 0, n_big - 1)]
    result7 = process_queries(n_big, ops7)
    assert result7 == [n_big], f"Large boundary test failed: {result7}"

    print("All self-tests passed.")
