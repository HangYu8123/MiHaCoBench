"""Generate the oracle-grounded mutation corpus for swe_bench/swe01_event_bus.

Independent oracle: a from-scratch, structurally-different event bus (pure dict +
list, no sort helper) that implements the same pub-sub contract but shares ZERO
code with the gold. The gold cross-validates against the oracle on every kept input.

The task is STATEFUL (EventBus is an object), so we wrap it into a pure function:
``run_ops(op_script)`` builds a fresh EventBus, replays a list of operations, and
returns the list of publish results. The oracle implements the SAME protocol with
its own reference bus. The gold and wrong wrappers are parameterised by the module
files dict so mutants can swap in a mutated registry.py while keeping bus.py and
events.py unchanged.

Key: every multi-file wrapper uses ``_load_event_bus_isolated`` which writes files to
a FRESH isolated tempdir and cleanly manages sys.modules, avoiding contamination
between gold and broken calls.

Provenance: Observer/pub-sub — handler not removed on unsubscribe (identity-
comparison failure) — cf. RxJS issue #4230.  Grader ground truth: independent
reference event bus.

Run:  python3 experiment_mihaco/mutation_gen/gen_swe01_event_bus.py
"""
from __future__ import annotations

import importlib.util
import random
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "swe_bench", "swe01_event_bus"
GOLD_DIR   = gu.GOLD_ROOT / CATEGORY / TASK_ID
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / f"{TASK_ID}__broken"

# Source texts for the multi-file gold
_BUS_SRC             = (GOLD_DIR / "bus.py").read_text()
_EVENTS_SRC          = (GOLD_DIR / "events.py").read_text()
_REGISTRY_SRC        = (GOLD_DIR / "registry.py").read_text()
_BROKEN_REGISTRY_SRC = (BROKEN_DIR / "registry.py").read_text()


# --------------------------------------------------------------------------- #
# Isolated package loader
# --------------------------------------------------------------------------- #
def _load_event_bus_isolated(files: dict[str, str]):
    """Write files to a fresh tempdir, isolate sys.modules, import bus.py.

    Returns (EventBus, Event) from the freshly loaded package.  Properly manages
    sys.modules['registry'] and sys.modules['events'] so bus.py's internal imports
    resolve to the files we just wrote, not to any previously loaded versions.
    """
    d = Path(tempfile.mkdtemp(prefix="evbus_"))
    for fname, src in files.items():
        (d / fname).write_text(src)

    # Save and remove existing 'registry'/'events' from sys.modules so bus.py's
    # `from registry import Registry` and `from events import Event` re-import fresh.
    old_registry = sys.modules.pop("registry", None)
    old_events   = sys.modules.pop("events",   None)
    sys.path.insert(0, str(d))
    try:
        # Load events.py under its canonical name (needed by dataclass __module__)
        ev_spec = importlib.util.spec_from_file_location("events", d / "events.py")
        ev_mod  = importlib.util.module_from_spec(ev_spec)
        sys.modules["events"] = ev_mod
        ev_spec.loader.exec_module(ev_mod)

        # Load registry.py under its canonical name
        reg_spec = importlib.util.spec_from_file_location("registry", d / "registry.py")
        reg_mod  = importlib.util.module_from_spec(reg_spec)
        sys.modules["registry"] = reg_mod
        reg_spec.loader.exec_module(reg_mod)

        # Load bus.py under a unique name to avoid module cache collisions
        bus_name = f"bus_{uuid.uuid4().hex}"
        bus_spec = importlib.util.spec_from_file_location(bus_name, d / "bus.py")
        bus_mod  = importlib.util.module_from_spec(bus_spec)
        sys.modules[bus_name] = bus_mod
        bus_spec.loader.exec_module(bus_mod)

        return getattr(bus_mod, "EventBus"), getattr(bus_mod, "Event")
    finally:
        sys.path.remove(str(d))
        # Restore original events/registry (or remove if they weren't present)
        if old_events is not None:
            sys.modules["events"]   = old_events
        else:
            sys.modules.pop("events", None)
        if old_registry is not None:
            sys.modules["registry"] = old_registry
        else:
            sys.modules.pop("registry", None)


def _make_run_ops_from_files(files: dict[str, str]) -> Callable:
    """Return run_ops(op_script) backed by the given files dict."""

    def run_ops(op_script: list) -> list:
        EventBus, Event = _load_event_bus_isolated(files)
        bus = EventBus()
        handlers: dict[int, Callable] = {}
        results: list = []
        for op in op_script:
            if op[0] == "sub":
                _, name, hid, prio = op
                if hid not in handlers:
                    def make_handler(i):
                        def h(ev):
                            return i
                        return h
                    handlers[hid] = make_handler(hid)
                bus.subscribe(name, handlers[hid], priority=prio)
            elif op[0] == "unsub":
                _, name, hid = op
                if hid in handlers:
                    bus.unsubscribe(name, handlers[hid])
            elif op[0] == "pub":
                _, name = op
                ev = Event(name)
                results.append(bus.publish(ev))
        return results

    return run_ops


# Gold wrapper
gold = _make_run_ops_from_files({
    "bus.py":      _BUS_SRC,
    "events.py":   _EVENTS_SRC,
    "registry.py": _REGISTRY_SRC,
})


# --------------------------------------------------------------------------- #
# Independent oracle — from-scratch reference bus (shares ZERO code with gold)
# --------------------------------------------------------------------------- #
def oracle(op_script: list) -> list:
    """Replay op_script on a reference event bus (dict-based, no sort helper).

    Re-subscribing an existing handler updates priority IN-PLACE (preserving its
    position in the bucket before the sort), then stably sorts by priority
    descending.  This matches the gold's in-place update + stable sort semantics.
    """
    # subs: name -> list of [priority, hid]  (mutable so in-place update works)
    subs: dict[str, list] = {}
    results: list = []

    for op in op_script:
        if op[0] == "sub":
            _, name, hid, prio = op
            bucket = subs.setdefault(name, [])
            # In-place update if already present (mirrors gold's bucket[i] = (prio, handler))
            updated = False
            for entry in bucket:
                if entry[1] == hid:
                    entry[0] = prio
                    updated = True
                    break
            if not updated:
                bucket.append([prio, hid])
            # Stable sort descending by priority (mirrors gold's bucket.sort(…, reverse=True))
            bucket.sort(key=lambda x: x[0], reverse=True)
        elif op[0] == "unsub":
            _, name, hid = op
            if name in subs:
                subs[name] = [e for e in subs[name] if e[1] != hid]
        elif op[0] == "pub":
            _, name = op
            bucket = subs.get(name, [])
            results.append([e[1] for e in bucket])

    return results


# --------------------------------------------------------------------------- #
# Wrong solutions
# --------------------------------------------------------------------------- #

# Hand-written wrong buses (self-contained, no external imports)
_WRONG_NEVER_REMOVES_SRC = '''
class _Reg:
    def __init__(self):
        self._s = {}
    def add(self, name, handler, priority=0):
        b = self._s.setdefault(name, [])
        for i,(p,h) in enumerate(b):
            if h is handler:
                b[i] = (priority, h)
                b.sort(key=lambda x: -x[0])
                return
        b.append((priority, handler))
        b.sort(key=lambda x: -x[0])
    def remove(self, name, handler):
        pass  # BUG: no-op, never removes any handler
    def handlers(self, name):
        return list(self._s.get(name, []))

class Event:
    def __init__(self, name, payload=None):
        self.name = name
        self.payload = payload

class EventBus:
    def __init__(self):
        self._r = _Reg()
    def subscribe(self, name, handler, priority=0):
        self._r.add(name, handler, priority)
    def unsubscribe(self, name, handler):
        self._r.remove(name, handler)
    def publish(self, event):
        return [h(event) for (p,h) in self._r.handlers(event.name)]
'''

_WRONG_REMOVES_ALL_SRC = '''
class _Reg:
    def __init__(self):
        self._s = {}
    def add(self, name, handler, priority=0):
        b = self._s.setdefault(name, [])
        for i,(p,h) in enumerate(b):
            if h is handler:
                b[i] = (priority, h)
                b.sort(key=lambda x: -x[0])
                return
        b.append((priority, handler))
        b.sort(key=lambda x: -x[0])
    def remove(self, name, handler):
        # BUG: clears ALL handlers for the name, not just the target
        self._s[name] = []
    def handlers(self, name):
        return list(self._s.get(name, []))

class Event:
    def __init__(self, name, payload=None):
        self.name = name
        self.payload = payload

class EventBus:
    def __init__(self):
        self._r = _Reg()
    def subscribe(self, name, handler, priority=0):
        self._r.add(name, handler, priority)
    def unsubscribe(self, name, handler):
        self._r.remove(name, handler)
    def publish(self, event):
        return [h(event) for (p,h) in self._r.handlers(event.name)]
'''

_WRONG_REVERSE_PRIORITY_SRC = '''
class _Reg:
    def __init__(self):
        self._s = {}
    def add(self, name, handler, priority=0):
        b = self._s.setdefault(name, [])
        for i,(p,h) in enumerate(b):
            if h is handler:
                b[i] = (priority, h)
                b.sort(key=lambda x: x[0])  # BUG: ascending (lowest priority first)
                return
        b.append((priority, handler))
        b.sort(key=lambda x: x[0])  # BUG: ascending
    def remove(self, name, handler):
        b = self._s.get(name)
        if not b:
            return
        self._s[name] = [(p,h) for (p,h) in b if h is not handler]
    def handlers(self, name):
        return list(self._s.get(name, []))

class Event:
    def __init__(self, name, payload=None):
        self.name = name
        self.payload = payload

class EventBus:
    def __init__(self):
        self._r = _Reg()
    def subscribe(self, name, handler, priority=0):
        self._r.add(name, handler, priority)
    def unsubscribe(self, name, handler):
        self._r.remove(name, handler)
    def publish(self, event):
        return [h(event) for (p,h) in self._r.handlers(event.name)]
'''

_WRONG_WRONG_KEY_SRC = '''
class _Reg:
    def __init__(self):
        self._s = {}
    def add(self, name, handler, priority=0):
        b = self._s.setdefault(name, [])
        for i,(p,h) in enumerate(b):
            if h is handler:
                b[i] = (priority, h)
                b.sort(key=lambda x: -x[0])
                return
        b.append((priority, handler))
        b.sort(key=lambda x: -x[0])
    def remove(self, name, handler):
        # BUG: looks up wrong key — same as the planted __broken registry bug
        wrong_key = name + "_unsub"
        b = self._s.get(wrong_key)
        if not b:
            return
        self._s[wrong_key] = [(p,h) for (p,h) in b if h is not handler]
    def handlers(self, name):
        return list(self._s.get(name, []))

class Event:
    def __init__(self, name, payload=None):
        self.name = name
        self.payload = payload

class EventBus:
    def __init__(self):
        self._r = _Reg()
    def subscribe(self, name, handler, priority=0):
        self._r.add(name, handler, priority)
    def unsubscribe(self, name, handler):
        self._r.remove(name, handler)
    def publish(self, event):
        return [h(event) for (p,h) in self._r.handlers(event.name)]
'''


def _make_wrong_run_ops_from_src(src: str) -> Callable:
    """Compile a self-contained wrong bus source and return run_ops wrapper."""
    ns: dict = {}
    exec(compile(src, "<wrong_bus>", "exec"), ns)  # noqa: S102
    _EventBus = ns["EventBus"]
    _Event    = ns["Event"]

    def run_ops(op_script: list) -> list:
        bus = _EventBus()
        handlers: dict[int, Callable] = {}
        results: list = []
        for op in op_script:
            if op[0] == "sub":
                _, name, hid, prio = op
                if hid not in handlers:
                    def make_handler(i):
                        def h(ev):
                            return i
                        return h
                    handlers[hid] = make_handler(hid)
                bus.subscribe(name, handlers[hid], priority=prio)
            elif op[0] == "unsub":
                _, name, hid = op
                if hid in handlers:
                    bus.unsubscribe(name, handlers[hid])
            elif op[0] == "pub":
                _, name = op
                ev = _Event(name)
                results.append(bus.publish(ev))
        return results

    return run_ops


def _wrong_fns():
    wrongs = []

    # 1. The real __broken (registry.py uses wrong key in remove)
    #    Use gold bus.py + events.py but BROKEN registry.py for proper isolation
    try:
        broken_files = {
            "bus.py":      _BUS_SRC,
            "events.py":   _EVENTS_SRC,
            "registry.py": _BROKEN_REGISTRY_SRC,
        }
        wrongs.append(("__broken", _make_run_ops_from_files(broken_files)))
    except Exception as e:
        print(f"WARNING: could not load __broken: {e}")

    # 2. AST mutants of registry.py (zero mutants expected — no eligible nodes)
    for label, mutant_registry in ms.generate_mutants(_REGISTRY_SRC):
        try:
            fn = _make_run_ops_from_files({
                "registry.py": mutant_registry,
                "bus.py":      _BUS_SRC,
                "events.py":   _EVENTS_SRC,
            })
            wrongs.append((label, fn))
        except Exception:
            continue

    # 3. Hand-written common-mistake wrong buses
    for name, src in [
        ("never_removes",  _WRONG_NEVER_REMOVES_SRC),
        ("removes_all",    _WRONG_REMOVES_ALL_SRC),
        ("reverse_prio",   _WRONG_REVERSE_PRIORITY_SRC),
        ("wrong_key_bug",  _WRONG_WRONG_KEY_SRC),
    ]:
        try:
            wrongs.append((name, _make_wrong_run_ops_from_src(src)))
        except Exception as e:
            print(f"WARNING: hand-written wrong '{name}' failed: {e}")

    return wrongs


# --------------------------------------------------------------------------- #
# Input generator
# --------------------------------------------------------------------------- #
_NAMES = ["alpha", "beta", "gamma", "delta"]
_HIDS  = [1, 2, 3, 4, 5]
_PRIOS = [-1, 0, 1, 2, 5, 10]


def _gen_inputs(seed: int = 20260616, n: int = 3000):
    rng = random.Random(seed)
    inputs = []

    def rand_name():
        return rng.choice(_NAMES)

    def rand_hid():
        return rng.choice(_HIDS)

    def rand_prio():
        return rng.choice(_PRIOS)

    for _ in range(n):
        script = []
        n_ops = rng.randint(3, 14)
        for _ in range(n_ops):
            r = rng.random()
            if r < 0.40:
                script.append(["sub", rand_name(), rand_hid(), rand_prio()])
            elif r < 0.60:
                script.append(["unsub", rand_name(), rand_hid()])
            else:
                script.append(["pub", rand_name()])
        inputs.append((script,))

    # Explicit high-value edge-case scripts targeting the planted bug and common mistakes
    explicit = [
        # sub-then-unsub-then-pub: removed handler must not appear
        ([["sub", "a", 1, 0], ["pub", "a"], ["unsub", "a", 1], ["pub", "a"]],),
        # unsub one of several: only the target disappears
        ([["sub", "a", 1, 0], ["sub", "a", 2, 0], ["pub", "a"],
          ["unsub", "a", 1], ["pub", "a"]],),
        # resubscribe after unsub
        ([["sub", "a", 1, 5], ["unsub", "a", 1], ["sub", "a", 1, 0], ["pub", "a"]],),
        # unsub from different name does not affect other name
        ([["sub", "a", 1, 0], ["sub", "b", 1, 0], ["unsub", "a", 1],
          ["pub", "a"], ["pub", "b"]],),
        # priority ordering (distinct priorities)
        ([["sub", "x", 1, 0], ["sub", "x", 2, 10], ["sub", "x", 3, 5], ["pub", "x"]],),
        # multiple events, different handlers
        ([["sub", "alpha", 1, 0], ["sub", "beta", 2, 0], ["pub", "alpha"], ["pub", "beta"]],),
        # subscribe same handler twice (update priority)
        ([["sub", "a", 1, 0], ["sub", "a", 1, 10], ["pub", "a"]],),
        # empty pub (no subscribers)
        ([["pub", "alpha"]],),
        # unsub non-existent handler (no-op)
        ([["unsub", "a", 99], ["sub", "a", 1, 0], ["pub", "a"]],),
        # multiple pubs after partial unsub
        ([["sub", "a", 1, 0], ["sub", "a", 2, 5], ["pub", "a"],
          ["unsub", "a", 2], ["pub", "a"], ["pub", "a"]],),
        # unsub target handler with higher priority (leaves lower-priority one)
        ([["sub", "a", 1, 5], ["sub", "a", 2, 0], ["unsub", "a", 1], ["pub", "a"]],),
        # multiple unsubs of same handler (idempotent)
        ([["sub", "a", 1, 0], ["unsub", "a", 1], ["unsub", "a", 1], ["pub", "a"]],),
        # handler on multiple events, unsub from one, still on the other
        ([["sub", "a", 1, 0], ["sub", "b", 1, 0], ["pub", "a"], ["pub", "b"],
          ["unsub", "a", 1], ["pub", "a"], ["pub", "b"]],),
        # removes_all check: two handlers, unsub one, other must remain
        ([["sub", "a", 1, 0], ["sub", "a", 2, 0], ["unsub", "a", 1],
          ["sub", "a", 3, 0], ["pub", "a"]],),
    ]
    inputs.extend(explicit)
    return inputs


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    wrongs = _wrong_fns()
    print(f"Total wrong solutions: {len(wrongs)}")

    inputs = _gen_inputs()
    print(f"Total inputs generated: {len(inputs)}")

    corpus = ms.build_corpus(gold, oracle, wrongs, inputs, max_keep=120)
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "independent-reference",
        "provenance": (
            "Observer/pub-sub: handler not removed on unsubscribe (identity-comparison failure) "
            "— cf. RxJS issue #4230. Grader ground truth: independent reference event bus."
        ),
        "input_seed": 20260616,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
