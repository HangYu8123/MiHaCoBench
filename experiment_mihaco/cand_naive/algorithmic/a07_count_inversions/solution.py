def count_inversions(nums: list[int]) -> int:
    """Return the number of inversion pairs (i, j) with i < j and nums[i] > nums[j].

    Equal elements are NOT considered an inversion.
    """
    if len(nums) <= 1:
        return 0

    arr = list(nums)  # do not mutate the input

    def merge_sort(a):
        if len(a) <= 1:
            return a, 0
        mid = len(a) // 2
        left, left_inv = merge_sort(a[:mid])
        right, right_inv = merge_sort(a[mid:])
        merged, split_inv = merge(left, right)
        return merged, left_inv + right_inv + split_inv

    def merge(left, right):
        result = []
        inversions = 0
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                # left[i] > right[j]: every remaining element in left forms an inversion with right[j]
                inversions += len(left) - i
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result, inversions

    _, total_inversions = merge_sort(arr)
    return int(total_inversions)
