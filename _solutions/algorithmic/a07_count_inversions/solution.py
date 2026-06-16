"""Gold reference for algorithmic/a07_count_inversions.

Counts the number of inversion pairs (i, j) with i < j and nums[i] > nums[j]
using a modified merge-sort algorithm.

Time complexity:  O(n log n)
Space complexity: O(n)  — temporary merge buffer
"""
from __future__ import annotations


def count_inversions(nums: list[int]) -> int:
    """Return the number of inversion pairs (i, j) with i < j and nums[i] > nums[j].

    Equal elements are NOT considered an inversion.

    Uses a modified merge-sort: while merging two sorted halves, whenever an
    element from the right half is placed before elements remaining in the left
    half, those left-half elements all form inversions with it.

    The input list is never mutated.
    """
    if len(nums) <= 1:
        return 0
    # Work on a copy so the caller's list is never mutated.
    arr = list(nums)
    _, inversions = _merge_sort(arr)
    return inversions


def _merge_sort(arr: list[int]) -> tuple[list[int], int]:
    """Sort *arr* in place and return (sorted_arr, inversion_count).

    Returns a new sorted list and the count; the input arr may be modified.
    """
    n = len(arr)
    if n <= 1:
        return arr, 0

    mid = n // 2
    left, left_inv = _merge_sort(arr[:mid])
    right, right_inv = _merge_sort(arr[mid:])

    merged = []
    inversions = left_inv + right_inv
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            # left[i] > right[j]: every remaining element in left is > right[j]
            inversions += len(left) - i
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged, inversions
