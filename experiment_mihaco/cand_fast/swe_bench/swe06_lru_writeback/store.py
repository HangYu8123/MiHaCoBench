class Backing:
    def __init__(self) -> None:
        """Create an empty dict-backed store."""
        self._data = {}

    def get(self, key):
        """Return the value stored under `key`, or raise KeyError if absent."""
        return self._data[key]

    def set(self, key, value) -> None:
        """Insert or overwrite the value stored under `key`."""
        self._data[key] = value
