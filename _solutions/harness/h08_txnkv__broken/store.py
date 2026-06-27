"""Gold reference — transactional in-memory key-value store.

See ``tasks/harness/h08_txnkv/TASK.md`` for the full public contract. This module
implements the :class:`Store` class; the per-frame undo/savepoint bookkeeping
lives in :mod:`frames`.

Conceptual model
----------------
The *visible state* a read observes is the committed store overlaid by the active
transaction stack (bottom → top), with TTL expiry applied against the current
logical clock. Writes inside a transaction are buffered in that frame; a buffered
delete is a *tombstone* that shadows lower layers as absent. ``commit`` merges the
top frame into the layer below; ``rollback`` discards it. Savepoints (within the
innermost frame only) allow undoing back to a named point while keeping the
transaction open.

TTL is stored as an *absolute* expiry time, computed from ``now()`` at the moment
of the ``set``, and is evaluated against the current clock only at read time —
never at commit time.
"""
from __future__ import annotations

from frames import TOMBSTONE, Frame, Write


class Store:
    """Single-threaded transactional KV store with savepoints and per-key TTL."""

    def __init__(self) -> None:
        # Committed layer: key -> Write(value, expiry).
        self._committed: dict[str, Write] = {}
        # Transaction stack; index -1 is the innermost (top) frame.
        self._stack: list[Frame] = []
        self._clock: int = 0

    # ------------------------------------------------------------------ #
    # Logical clock
    # ------------------------------------------------------------------ #
    def now(self) -> int:
        """Return the current logical time (starts at 0)."""
        return self._clock

    def tick(self, dt: int) -> None:
        """Advance the logical clock by ``dt`` (``dt >= 0``)."""
        if dt < 0:
            raise ValueError(f"dt must be >= 0, got {dt}")
        self._clock += dt

    # ------------------------------------------------------------------ #
    # Visibility helpers
    # ------------------------------------------------------------------ #
    def _resolve(self, key: str):
        """Return the topmost buffer/committed entry for ``key`` ignoring TTL.

        Returns a :class:`Write`, the ``TOMBSTONE`` sentinel, or ``None`` when no
        layer mentions the key.
        """
        for frame in reversed(self._stack):
            if key in frame.buffer:
                return frame.buffer[key]
        return self._committed.get(key)

    def _expired(self, entry: Write) -> bool:
        return entry.expiry is not None and self._clock >= entry.expiry

    def _live_value(self, key: str) -> str | None:
        """Current visible value for ``key`` with TTL applied, else ``None``."""
        entry = self._resolve(key)
        if entry is None or entry is TOMBSTONE:
            return None
        if self._expired(entry):
            return None
        return entry.value

    def _top(self) -> Frame:
        if not self._stack:
            raise ValueError("no active transaction")
        return self._stack[-1]

    # ------------------------------------------------------------------ #
    # Core operations
    # ------------------------------------------------------------------ #
    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set ``key=value``; with ``ttl`` (``> 0``) it expires at ``now()+ttl``.

        ``ttl=None`` clears any prior expiry on the key.
        """
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be > 0, got {ttl}")
        expiry = None if ttl is None else self._clock + ttl
        entry = Write(value, expiry)
        if self._stack:
            self._top().apply(key, entry)
        else:
            self._committed[key] = entry

    def get(self, key: str) -> str | None:
        """Return the current visible value, or ``None`` if absent/expired."""
        return self._live_value(key)

    def delete(self, key: str) -> bool:
        """Remove ``key``; return whether it was present (and unexpired) before."""
        was_present = self._live_value(key) is not None
        if self._stack:
            # Buffer a tombstone so the key reads as absent within this frame and
            # the delete can be undone by rollback / rollback_to.
            self._top().apply(key, TOMBSTONE)
        else:
            self._committed.pop(key, None)
        return was_present

    def keys(self, prefix: str = "") -> list[str]:
        """Sorted currently-present (unexpired) keys starting with ``prefix``."""
        candidates: set[str] = set(self._committed)
        for frame in self._stack:
            candidates.update(frame.buffer)
        out = [
            k for k in candidates
            if k.startswith(prefix) and self._live_value(k) is not None
        ]
        return sorted(out)

    # ------------------------------------------------------------------ #
    # Transactions
    # ------------------------------------------------------------------ #
    def begin(self) -> None:
        """Push a new transaction frame onto the stack."""
        self._stack.append(Frame())

    def commit(self) -> None:
        """Pop the top frame and merge its buffered writes into the layer below."""
        frame = self._top()
        self._stack.pop()
        if self._stack:
            lower = self._stack[-1]
            for key, entry in frame.buffer.items():
                lower.apply(key, entry)
        else:
            for key, entry in frame.buffer.items():
                if entry is TOMBSTONE:
                    self._committed.pop(key, None)
                else:
                    self._committed[key] = entry

    def rollback(self) -> None:
        """Pop and discard the top frame (its writes and savepoints)."""
        self._top()  # raises ValueError if no active transaction
        self._stack.pop()

    # ------------------------------------------------------------------ #
    # Savepoints (innermost frame only)
    # ------------------------------------------------------------------ #
    def savepoint(self, name: str) -> None:
        """Mark a named savepoint in the innermost transaction (re-mark moves it)."""
        self._top().savepoint(name)

    def rollback_to(self, name: str) -> None:
        """Undo writes since ``name`` in the innermost txn; keep the txn + ``name``."""
        frame = self._top()
        if not frame.has_savepoint(name):
            raise ValueError(f"unknown savepoint: {name!r}")
        frame.rollback_to(name)

    def release(self, name: str) -> None:
        """Forget ``name`` (and savepoints set after it) without undoing writes."""
        frame = self._top()
        if not frame.has_savepoint(name):
            raise ValueError(f"unknown savepoint: {name!r}")
        frame.release(name)
