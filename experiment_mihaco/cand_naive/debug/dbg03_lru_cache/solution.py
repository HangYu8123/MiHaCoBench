from collections import OrderedDict


class RecentCache:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key) -> object:
        if key not in self._data:
            return None
        self._data.move_to_end(key)  # mark as most-recently-used
        return self._data[key]

    def put(self, key, value) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)  # evict least-recently-used
