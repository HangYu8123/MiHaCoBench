def count_inversions(nums: list[int]) -> int:
    """Return the number of inversion pairs (i, j) with i < j and nums[i] > nums[j].

    Equal elements are NOT considered an inversion.
    """
    def merge_sort(arr: list[int]) -> tuple[list[int], int]:
        if len(arr) <= 1:
            return arr, 0

        mid = len(arr) // 2
        left, left_count = merge_sort(arr[:mid])
        right, right_count = merge_sort(arr[mid:])

        merged = []
        count = left_count + right_count
        i = j = 0

        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                # Equal or left is smaller: take from left, no inversion
                merged.append(left[i])
                i += 1
            else:
                # left[i] > right[j]: all remaining left elements invert with right[j]
                count += len(left) - i
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    # Work on a copy to avoid mutating the input
    arr = list(nums)
    _, total = merge_sort(arr)
    return int(total)
