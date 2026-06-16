"""Gold reference for competitive/cp01_range_query.

Range update + range sum using a dual Fenwick Binary Indexed Tree (BIT).

Theory (0-indexed arrays with 0-indexed BIT internally shifted to 1-indexed):
  prefix_sum(i) = B1.query(i) * (i+1) - B2.query(i)
where B1 and B2 are standard point-update / prefix-query BITs.

For a range add of v on [l, r] (0-indexed):
  - Update the difference array: diff[l] += v, diff[r+1] -= v
  - B1 stores the difference array (for O(log n) prefix queries of it)
  - B2 stores k*diff[k] so prefix_sum can subtract the weighted part

This gives O(log n) per add and O(log n) per sum query, so the total
complexity for q operations on a size-n array is O((n + q) log n).
"""
from __future__ import annotations


def process_queries(n: int, ops: list[tuple]) -> list[int]:
    """Process range-add and range-sum queries on an array of n zeros.

    Each op is either ("add", l, r, v) or ("sum", l, r).
    Returns a list of results for all "sum" ops in order.

    Time complexity:  O((n + q) log n) where q = len(ops)
    Space complexity: O(n)
    """
    # 0-indexed BIT, size n+1 so we can safely query index n-1.
    # We use 1-indexed internal storage (index 0 unused) of size n+1.
    size = n + 1  # valid 1-indexed positions: 1 .. n

    # B1[i] stores difference-array values; B2[i] stores k*diff[k]
    b1 = [0] * (size + 1)
    b2 = [0] * (size + 1)

    def _update(tree: list, i: int, delta: int) -> None:
        """Add delta to 1-indexed position i and propagate up."""
        while i <= size:
            tree[i] += delta
            i += i & (-i)

    def _prefix(tree: list, i: int) -> int:
        """Return prefix sum tree[1..i] (1-indexed)."""
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    def _range_add(l: int, r: int, v: int) -> None:
        """Add v to every element in [l, r] (0-indexed)."""
        # Convert to 1-indexed: l0 -> l+1, r0 -> r+1
        l1 = l + 1
        r1 = r + 1
        _update(b1, l1, v)
        _update(b1, r1 + 1, -v)
        _update(b2, l1, v * l)   # v * (l1 - 1) = v * l (0-indexed l)
        _update(b2, r1 + 1, -v * (r + 1))  # -v * r1 = -v * (r+1) [0-indexed r+1]

    def _prefix_sum(i: int) -> int:
        """Return sum of arr[0..i] (0-indexed, inclusive)."""
        i1 = i + 1  # 1-indexed position
        # prefix_sum(i) = B1_prefix(i) * (i+1) - B2_prefix(i)
        # where B1_prefix(i) = sum of diff[0..i] = arr[i+1] conceptually
        return _prefix(b1, i1) * (i + 1) - _prefix(b2, i1)

    def _range_sum(l: int, r: int) -> int:
        """Return sum of arr[l..r] (0-indexed, inclusive)."""
        result = _prefix_sum(r)
        if l > 0:
            result -= _prefix_sum(l - 1)
        return result

    results: list[int] = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            _range_add(l, r, v)
        else:
            _, l, r = op
            results.append(_range_sum(l, r))
    return results
