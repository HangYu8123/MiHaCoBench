class Backing:
    def __init__(self) -> None:
        """Create an empty dict-backed store."""
        self._store = {}

    def get(self, key):
        """Return the value stored under `key`, or raise KeyError if absent."""
        if key not in self._store:
            raise KeyError(key)
        return self._store[key]

    def set(self, key, value) -> None:
        """Insert or overwrite the value stored under `key`."""
        self._store[key] = value
