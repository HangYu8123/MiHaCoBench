MISS = object()  # module-level sentinel; distinct from None


class _Node:
    """Doubly-linked-list node storing a key/value pair."""
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRU:
    """Hand-rolled LRU cache backed by a doubly-linked list + dict."""

    def __init__(self, capacity: int) -> None:
        """Create a cache holding at most `capacity` entries (capacity >= 1)."""
        self._capacity = capacity
        self._map = {}  # key -> _Node

        # Sentinel head (LRU end) and tail (MRU end) nodes.
        self._head = _Node(None, None)  # LRU sentinel
        self._tail = _Node(None, None)  # MRU sentinel
        self._head.next = self._tail
        self._tail.prev = self._head

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _remove(self, node: _Node) -> None:
        """Unlink `node` from the doubly-linked list."""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_at_tail(self, node: _Node) -> None:
        """Link `node` just before the tail sentinel (MRU position)."""
        prev = self._tail.prev
        prev.next = node
        node.prev = prev
        node.next = self._tail
        self._tail.prev = node

    def _move_to_front(self, node: _Node) -> None:
        """Move an already-linked node to the MRU (tail) position."""
        self._remove(node)
        self._insert_at_tail(node)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key):
        """Return the cached value and mark `key` MRU, or return MISS."""
        node = self._map.get(key)
        if node is None:
            return MISS
        self._move_to_front(node)
        return node.value

    def put(self, key, value) -> None:
        """Insert OR update `key` with `value` and mark it MRU.

        - A NEW key is inserted; if the cache would exceed `capacity`, the
          LEAST-recently-used key is evicted first.
        - An EXISTING key has its stored value OVERWRITTEN with `value` and is
          marked most-recently-used.
        """
        if key in self._map:
            # THE FIX: overwrite the stored value, then bump recency.
            node = self._map[key]
            node.value = value          # overwrite — was missing in the buggy version
            self._move_to_front(node)
            return

        # New key: evict LRU entry if at capacity.
        if len(self._map) >= self._capacity:
            lru_node = self._head.next  # node just after head sentinel is LRU
            self._remove(lru_node)
            del self._map[lru_node.key]

        # Insert the new node at MRU position.
        new_node = _Node(key, value)
        self._insert_at_tail(new_node)
        self._map[key] = new_node

    def invalidate(self, key) -> None:
        """Drop `key` from the cache if present (no-op when absent)."""
        node = self._map.pop(key, None)
        if node is not None:
            self._remove(node)
