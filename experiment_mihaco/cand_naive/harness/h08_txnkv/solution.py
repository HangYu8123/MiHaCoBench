"""In-memory transactional KV store with savepoints and TTL (naive single-pass)."""

from bisect import insort


_SET = "set"
_DEL = "del"


class _Frame:
    __slots__ = ("ops", "store", "savepoints", "sp_order")

    def __init__(self):
        self.ops = []            # list of (key, entry)
        self.store = {}          # key -> entry (materialized overlay)
        self.savepoints = {}     # name -> int position in ops
        self.sp_order = []       # names in creation order

    def _rebuild(self):
        store = {}
        for key, entry in self.ops:
            store[key] = entry
        self.store = store

    def apply(self, key, entry):
        self.ops.append((key, entry))
        self.store[key] = entry

    def truncate_to(self, pos):
        if pos < len(self.ops):
            del self.ops[pos:]
            self._rebuild()


class Store:
    def __init__(self):
        self._committed = {}     # key -> (value, expiry_or_None)
        self._stack = []         # list of _Frame, bottom -> top
        self._clock = 0

    def now(self):
        return self._clock

    def tick(self, dt):
        if not isinstance(dt, bool) and isinstance(dt, int) and dt >= 0:
            self._clock += dt
            return None
        if isinstance(dt, int) and not isinstance(dt, bool):
            raise ValueError("dt must be >= 0")
        raise ValueError("dt must be a non-negative integer")

    def _is_expired(self, expiry):
        return expiry is not None and self._clock >= expiry

    def _lookup(self, key):
        for frame in reversed(self._stack):
            entry = frame.store.get(key)
            if entry is not None:
                return entry
        cm = self._committed.get(key)
        if cm is not None:
            value, expiry = cm
            return (_SET, value, expiry)
        return None

    def _visible_value(self, key):
        entry = self._lookup(key)
        if entry is None or entry[0] == _DEL:
            return None
        _, value, expiry = entry
        if self._is_expired(expiry):
            return None
        return value

    def _all_keys(self):
        seen = set()
        result = []
        for frame in reversed(self._stack):
            for key, entry in frame.store.items():
                if key in seen:
                    continue
                seen.add(key)
                if entry[0] == _SET and not self._is_expired(entry[2]):
                    result.append(key)
        for key, (value, expiry) in self._committed.items():
            if key in seen:
                continue
            seen.add(key)
            if not self._is_expired(expiry):
                result.append(key)
        return result

    def set(self, key, value, ttl=None):
        if ttl is not None:
            if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0:
                raise ValueError("ttl must be a positive integer when provided")
            expiry = self._clock + ttl
        else:
            expiry = None

        entry = (_SET, value, expiry)
        if self._stack:
            self._stack[-1].apply(key, entry)
        else:
            self._committed[key] = (value, expiry)

    def get(self, key):
        return self._visible_value(key)

    def delete(self, key):
        existed = self._visible_value(key) is not None
        if self._stack:
            self._stack[-1].apply(key, (_DEL,))
        else:
            self._committed.pop(key, None)
        return existed

    def keys(self, prefix=""):
        out = []
        for key in self._all_keys():
            if key.startswith(prefix):
                insort(out, key)
        return out

    def begin(self):
        self._stack.append(_Frame())

    def commit(self):
        if not self._stack:
            raise ValueError("no active transaction")
        top = self._stack.pop()
        if self._stack:
            lower = self._stack[-1]
            for key, entry in top.ops:
                lower.apply(key, entry)
        else:
            for key, entry in top.ops:
                if entry[0] == _DEL:
                    self._committed.pop(key, None)
                else:
                    _, value, expiry = entry
                    self._committed[key] = (value, expiry)

    def rollback(self):
        if not self._stack:
            raise ValueError("no active transaction")
        self._stack.pop()

    def savepoint(self, name):
        if not self._stack:
            raise ValueError("no active transaction")
        frame = self._stack[-1]
        if name in frame.savepoints:
            frame.sp_order.remove(name)
        frame.savepoints[name] = len(frame.ops)
        frame.sp_order.append(name)

    def rollback_to(self, name):
        if not self._stack:
            raise ValueError("no active transaction")
        frame = self._stack[-1]
        if name not in frame.savepoints:
            raise ValueError("unknown savepoint: %r" % (name,))
        pos = frame.savepoints[name]
        frame.truncate_to(pos)
        idx = frame.sp_order.index(name)
        discarded = frame.sp_order[idx + 1:]
        del frame.sp_order[idx + 1:]
        for sp in discarded:
            del frame.savepoints[sp]

    def release(self, name):
        if not self._stack:
            raise ValueError("no active transaction")
        frame = self._stack[-1]
        if name not in frame.savepoints:
            raise ValueError("unknown savepoint: %r" % (name,))
        idx = frame.sp_order.index(name)
        removed = frame.sp_order[idx:]
        del frame.sp_order[idx:]
        for sp in removed:
            del frame.savepoints[sp]
