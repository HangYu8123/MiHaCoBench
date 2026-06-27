import bisect
from collections import defaultdict


def kth_distinct_in_window(a: list, w: int, k: int) -> list:
    if w < 1 or k < 1:
        raise ValueError("w and k must be >= 1")
    n = len(a)
    if w > n:
        return []

    # freq[v] = count of v in current window
    freq = defaultdict(int)
    # sorted list of distinct values (maintained manually via bisect)
    distinct = []

    results = []

    # Initialize first window
    for i in range(w):
        val = a[i]
        if freq[val] == 0:
            bisect.insort(distinct, val)
        freq[val] += 1

    # Answer for first window
    if len(distinct) >= k:
        results.append(distinct[k - 1])
    else:
        results.append(None)

    # Slide window
    for i in range(1, n - w + 1):
        # Remove outgoing element a[i-1]
        out_val = a[i - 1]
        freq[out_val] -= 1
        if freq[out_val] == 0:
            idx = bisect.bisect_left(distinct, out_val)
            distinct.pop(idx)
            del freq[out_val]

        # Add incoming element a[i+w-1]
        in_val = a[i + w - 1]
        if freq[in_val] == 0:
            bisect.insort(distinct, in_val)
        freq[in_val] += 1

        if len(distinct) >= k:
            results.append(distinct[k - 1])
        else:
            results.append(None)

    return results
