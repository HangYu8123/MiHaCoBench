def count_inversions(nums: list[int]) -> int:
    """Return the number of inversion pairs (i, j) with i < j and nums[i] > nums[j].

    Equal elements are NOT considered an inversion.
    """

    def merge(left, right):
        result = []
        inversions = 0
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                inversions += len(left) - i
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result, inversions

    def merge_sort(arr):
        if len(arr) < 2:
            return arr, 0
        mid = len(arr) // 2
        left, left_inv = merge_sort(arr[:mid])
        right, right_inv = merge_sort(arr[mid:])
        merged, split_inv = merge(left, right)
        return merged, left_inv + right_inv + split_inv

    _, total = merge_sort(list(nums))
    return total
