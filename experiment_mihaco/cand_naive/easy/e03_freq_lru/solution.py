from collections import OrderedDict


class FreqLRU:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._capacity = capacity
        # OrderedDict maintains insertion order; we'll move items to end on access (MRU = end)
        self._cache = OrderedDict()  # key -> value
        self._freq = {}              # key -> access count

    def get(self, key) -> object:
        if key not in self._cache:
            return None
        # Hit: increment frequency, mark MRU
        self._freq[key] += 1
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key, value) -> None:
        if key in self._cache:
            # Update existing: increment freq, mark MRU, update value
            self._cache[key] = value
            self._freq[key] += 1
            self._cache.move_to_end(key)
        else:
            # New key
            if len(self._cache) == self._capacity:
                # Evict LRU (first item in OrderedDict)
                evicted_key, _ = self._cache.popitem(last=False)
                del self._freq[evicted_key]
            # Insert new key as MRU
            self._cache[key] = value
            self._freq[key] = 1
            # move_to_end not needed since newly inserted items go to end in OrderedDict

    def histogram(self) -> dict:
        return dict(self._freq)

    def __len__(self) -> int:
        return len(self._cache)
