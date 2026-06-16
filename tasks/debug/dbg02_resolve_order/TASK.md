# Debug 02 — `resolve_order`: a cycle that slips through

**Created:** 2026-06-15 · **Category:** debug · **Weight:** 2

You are given a **buggy** topological "load order" resolver. Find and fix the
defect, then write your corrected solution as `solution.py` (**standard library
only**). Keep the public contract below exactly; do not rename the function.

## Buggy implementation

```python
def resolve_load_order(dependencies):
    order = []
    visited = set()

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in dependencies.get(node, []):
            visit(dep)
        order.append(node)

    for node in sorted(dependencies):
        visit(node)
    return order
```

## Symptom (failing behavior)

Cyclic dependency graphs must be rejected with a `ValueError`, but the buggy
resolver silently returns an order instead:

```text
>>> resolve_load_order({"a": ["a"]})            # self-dependency
['a']                                            # actual   (wrong — should raise)
>>> resolve_load_order({"a": ["b"], "b": ["a"]}) # direct two-node cycle
['a', 'b']                                       # actual   (wrong — should raise)
```

Acyclic graphs are ordered correctly already — only cycle detection is broken.

## Public contract (must match exactly)

```python
def resolve_load_order(dependencies: dict[str, list[str]]) -> list[str]:
    ...
```

* `dependencies` maps each module to the list of modules it depends on (which
  must load **first**). Every referenced module also appears as a key.
* Return a list of all modules in an order where **every dependency precedes the
  module that requires it** (a valid topological order).
* Raise `ValueError` if the graph contains **any** cycle — including a
  self-dependency (`{"a": ["a"]}`) and a direct two-node cycle
  (`{"a": ["b"], "b": ["a"]}`).
* `resolve_load_order({})` returns `[]`.

## Notes

* Standard library only. Assert exceptions by **type** (`ValueError`), not message.
* Determinism: identical input ⇒ identical output.
