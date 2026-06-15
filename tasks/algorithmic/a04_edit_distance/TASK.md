# Algorithmic 04 — `edit_distance`: space-optimised Levenshtein distance

**Created:** 2026-06-15 · **Category:** algorithmic · **Weight:** 8

Implement the classic Levenshtein edit distance in a **single file** `solution.py`
using the **standard library only**.

## Public contract

```python
def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.
    """
```

## Complexity requirements (both are hard-gated in the grader)

| Requirement | Detail |
|---|---|
| **Time** | O(m · n) — for strings of length m and n respectively. A naïve exponential recursion will time out on the large inputs. |
| **Space** | O(min(m, n)) — use a rolling two-row (or single-row) DP array. A full O(m · n) matrix is **not acceptable** and will fail the memory gate. |

### Concrete gate values (in the grader)

* **Time gate:** strings of length **2000** each — must complete within **8 seconds**.
* **Space gate:** strings of length **1000** each — peak heap allocation from
  `tracemalloc` must be **< 5 000 000 bytes** (5 MB).
  A full `int` table of size 1001 × 1001 occupies roughly 36 MB of Python
  list-of-lists pointer overhead, far exceeding the limit; a single-row
  rolling array stays under 100 KB.

## Examples

```
edit_distance("", "abc")      == 3
edit_distance("abc", "")      == 3
edit_distance("abc", "abc")   == 0
edit_distance("kitten", "sitting") == 3
edit_distance("sunday", "saturday") == 3
edit_distance("a", "b")       == 1   # substitution
edit_distance("a", "ab")      == 1   # insertion
edit_distance("ab", "a")      == 1   # deletion
```

## Notes

* Symmetry must hold: `edit_distance(a, b) == edit_distance(b, a)`.
* The function is called with arbitrary Unicode strings; no length constraint beyond
  what is tested.
* Determinism: the result is an integer with no randomness.
