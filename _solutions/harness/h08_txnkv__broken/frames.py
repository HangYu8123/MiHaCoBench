"""Transaction-frame and savepoint machinery for the transactional KV store.

This module is intentionally separate from :mod:`store` so the visibility /
overlay logic (in :mod:`store`) is decoupled from the per-frame undo bookkeeping
that makes savepoints and rollbacks correct.

A *frame* is one level of the transaction stack. It buffers writes (so they are
visible to reads within the transaction but not yet committed) and records an
ordered undo log so that ``rollback_to(name)`` can precisely undo everything
written since a savepoint while keeping the transaction — and that savepoint —
open.

Buffer entries are one of:

* :class:`Write`   — a buffered ``set`` (carrying its absolute ``expiry`` time,
  or ``None`` for "no expiry"). Expiry is an *absolute* logical time computed
  from ``now()`` at the moment of the ``set``; it is evaluated against the
  current clock only at read time, never at commit time.
* :data:`TOMBSTONE` — a buffered ``delete``: within this frame the key reads as
  absent even if a lower/committed layer holds a value.

A key *not present* in a frame's buffer is "pass-through": the frame says
nothing about it and the next layer down decides its value.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Write:
    """A buffered ``set``: ``value`` with an absolute ``expiry`` time (or None)."""

    value: str
    expiry: int | None


class _Tombstone:
    """Singleton marker for a buffered ``delete`` (a key shadowed as absent)."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return "TOMBSTONE"


#: Sentinel buffer entry meaning "deleted within this frame".
TOMBSTONE = _Tombstone()

#: Sentinel for "this key was not present in the buffer" (used in the undo log).
_MISSING = object()

#: A buffer entry is either a Write, the TOMBSTONE sentinel.
Entry = object


class Frame:
    """One level of the transaction stack: a write buffer + an undo log.

    The undo log records, for every mutation applied to this frame, the *prior*
    buffer entry for the touched key (or :data:`_MISSING` if the key was not yet
    buffered). Undo simply replays those prior entries in reverse. Savepoints are
    recorded as ``(name, log_length_at_creation)`` in creation order; a savepoint
    therefore points at a position in the log, and ``rollback_to`` truncates the
    log back to that position.
    """

    __slots__ = ("buffer", "_log", "_savepoints")

    def __init__(self) -> None:
        self.buffer: dict[str, Entry] = {}
        # Undo log: list of (key, prior_entry_or__MISSING).
        self._log: list[tuple[str, object]] = []
        # Ordered list of (name, log_length_when_created).
        self._savepoints: list[tuple[str, int]] = []

    # -- mutation -------------------------------------------------------- #
    def apply(self, key: str, entry: Entry) -> None:
        """Buffer ``entry`` for ``key``, recording an undo record first."""
        self._log.append((key, self.buffer.get(key, _MISSING)))
        self.buffer[key] = entry

    # -- savepoints ------------------------------------------------------ #
    def savepoint(self, name: str) -> None:
        """Mark a named savepoint at the current log position.

        Re-marking an existing name moves it (and only it) to "now"; savepoints
        created after the old position keep their own positions.
        """
        self._savepoints = [(n, p) for (n, p) in self._savepoints if n != name]
        self._savepoints.append((name, len(self._log)))

    def has_savepoint(self, name: str) -> bool:
        return any(n == name for (n, _p) in self._savepoints)

    def rollback_to(self, name: str) -> None:
        """Undo every write made since ``name`` was set; keep the txn + ``name``.

        Savepoints set *after* ``name`` are discarded; ``name`` and any set
        before it remain valid. The transaction frame stays open.
        """
        target = self._savepoint_position(name)
        self._undo_to(target)
        # Keep savepoints created strictly before the target position.
        self._savepoints = [(n, p) for (n, p) in self._savepoints if p < target]

    def release(self, name: str) -> None:
        """Forget ``name`` and any savepoints set after it; undo nothing."""
        idx = self._savepoint_index(name)
        del self._savepoints[idx:]

    # -- internals ------------------------------------------------------- #
    def _savepoint_index(self, name: str) -> int:
        for i, (n, _p) in enumerate(self._savepoints):
            if n == name:
                return i
        raise KeyError(name)

    def _savepoint_position(self, name: str) -> int:
        for n, p in self._savepoints:
            if n == name:
                return p
        raise KeyError(name)

    def _undo_to(self, target_len: int) -> None:
        """Replay undo records until the log has length ``target_len``."""
        while len(self._log) > target_len:
            key, prior = self._log.pop()
            # A tombstone (buffered delete) is left in place rather than undone.
            if self.buffer.get(key) is TOMBSTONE:
                continue
            if prior is _MISSING:
                self.buffer.pop(key, None)
            else:
                self.buffer[key] = prior
