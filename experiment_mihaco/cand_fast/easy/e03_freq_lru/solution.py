from collections import OrderedDict


class FreqLRU:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        self._cap = capacity
        self._cache = OrderedDict()  # key -> [value, freq]

    def get(self, key) -> object:
        if key not in self._cache:
            return None
        self._cache[key][1] += 1
        self._cache.move_to_end(key)
        return self._cache[key][0]

    def put(self, key, value) -> None:
        if key in self._cache:
            # Update existing: increment freq, mark MRU, no eviction
            self._cache[key] = [value, self._cache[key][1] + 1]
            self._cache.move_to_end(key)
        else:
            # New key: evict LRU if at capacity, then insert
            if len(self._cache) == self._cap:
                self._cache.popitem(last=False)
            self._cache[key] = [value, 1]
            # New entry appended at end = MRU automatically

    def histogram(self) -> dict:
        return {k: v[1] for k, v in self._cache.items()}

    def __len__(self) -> int:
        return len(self._cache)
