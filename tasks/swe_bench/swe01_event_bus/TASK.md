# SWE-Bench 01 — `swe01_event_bus`: In-Memory Publish/Subscribe Event Bus

**Created:** 2026-06-15 · **Category:** swe_bench · **Weight:** 6

Implement a small in-memory publish/subscribe event bus spread across **at least
three files**.  The grader imports the public `Event`/`EventBus` from `bus.py`
**and** the `Registry` class from `registry.py` — both interfaces are documented
below and are part of the contract.

---

## Files to create (minimum)

```
events.py    — Event value type
registry.py  — subscriber storage per event name
bus.py       — PUBLIC FACADE: re-exports Event and class EventBus
```

---

## Public contract (all names must be importable from `bus.py`)

### `class Event`

An **immutable** value type with two attributes:

| Attribute | Type  | Description                                    |
|-----------|-------|------------------------------------------------|
| `name`    | `str` | Non-empty logical channel name, e.g. `"user.created"` |
| `payload` | `Any` | Arbitrary data; defaults to `None`             |

Constructing an `Event` with an empty or non-string `name` must raise
`ValueError`.

### `class EventBus`

| Method | Signature | Description |
|--------|-----------|-------------|
| `subscribe`   | `subscribe(name: str, handler: Callable, priority: int = 0) -> None` | Register *handler* for events named *name* at the given *priority*. Re-subscribing the same handler updates its priority. |
| `unsubscribe` | `unsubscribe(name: str, handler: Callable) -> None` | Remove *handler* from *name*'s subscriber list. No-op if not subscribed. |
| `publish`     | `publish(event: Event) -> list` | Call every handler subscribed to `event.name` in **descending priority order** (highest first). Return a **list** of each handler's return value, in call order. |

#### Ordering guarantee

Handlers registered with a **higher** `priority` integer are called **before**
handlers with a lower one.  Handlers with the same priority are called in
subscription order (the order in which `subscribe` was called).

### `class Registry` (in `registry.py`)

`registry.py` must expose a `Registry` class that holds the per-event-name
subscriber storage `EventBus` is built on. The grader exercises it directly, so
its interface is part of the public contract:

| Method | Signature | Description |
|--------|-----------|-------------|
| `add`      | `add(name: str, handler: Callable, priority: int = 0) -> None` | Store *handler* for *name* at *priority*. Re-adding the same handler updates its priority. |
| `remove`   | `remove(name: str, handler: Callable) -> None` | Remove *handler* from *name*. No-op if absent. |
| `handlers` | `handlers(name: str) -> list[tuple[int, Callable]]` | Return `(priority, handler)` pairs for *name* in **descending priority** order (highest first; ties in subscription order). Empty list if none. |

`Registry()` takes no required constructor arguments.

---

## Notes

- A handler that has been unsubscribed **must not** be called on subsequent
  `publish` calls — even if another handler for the same event is still
  subscribed.
- `publish` returns an empty list `[]` if no handlers are subscribed for
  `event.name`.
- Payloads may be any Python object (dict, list, int, None, …).
- Multiple `EventBus` instances must be independent of one another.
- The grader loads both `bus.py` **and** `registry.py` directly to run
  integration tests that span the bus ↔ registry boundary.

---

## Known symptom to avoid

A common implementation defect causes `unsubscribe` to silently do nothing,
so a handler that has been explicitly removed continues to receive all
subsequent published events.  Your implementation must not exhibit this
behaviour.
