"""FieldIndex: maps a field value -> set of keys carrying that value."""


class FieldIndex:
    def __init__(self):
        # field_value -> set of keys
        self._map = {}

    def add(self, key, field_value) -> None:
        if field_value not in self._map:
            self._map[field_value] = set()
        self._map[field_value].add(key)

    def remove(self, key, field_value) -> None:
        """No-op if absent."""
        bucket = self._map.get(field_value)
        if bucket is None:
            return
        bucket.discard(key)
        if not bucket:
            del self._map[field_value]

    def keys_with(self, field_value) -> set:
        """Return a copy of the key set for the given field value."""
        return set(self._map.get(field_value, set()))

    def all_indexed_keys(self) -> set:
        """Return the union of all key sets across all field values."""
        result = set()
        for bucket in self._map.values():
            result |= bucket
        return result
