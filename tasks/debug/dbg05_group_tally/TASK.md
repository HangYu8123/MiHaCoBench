# Debug 05 — `group_tally`: state leaks between calls

**Created:** 2026-06-15 · **Category:** debug · **Weight:** 2

You are given a **buggy** grouped-accumulation helper. Find and fix the defect,
then write your corrected solution as `solution.py` (**standard library only**).
Keep the public contract below exactly; do not rename the function or change its
parameters.

## Buggy implementation

```python
def tally_by_group(label, value, groups={}):
    groups.setdefault(label, []).append(value)
    return groups
```

## Symptom (failing behavior)

When called **without** a `groups` argument, each call should start from an empty
result. Instead, results from earlier calls leak into later ones:

```text
>>> tally_by_group("alpha", 1)
{'alpha': [1]}                 # ok
>>> tally_by_group("beta", 2)  # a separate, independent call
{'alpha': [1], 'beta': [2]}    # actual   (wrong — "alpha" leaked in)
{'beta': [2]}                  # expected
```

Calls that pass an explicit `groups` dict already accumulate correctly — only the
no-argument path is broken.

## Public contract (must match exactly)

```python
def tally_by_group(label: str, value, groups: dict | None = None) -> dict:
    ...
```

* Append `value` to the list at `groups[label]` (creating the list on first use)
  and return `groups`.
* When `groups` is omitted (or `None`), create and return a **fresh** dict, so
  independent calls never share state.
* When a `groups` dict is supplied, mutate it in place and return the same object
  (so a caller can accumulate across calls).

## Notes

* Standard library only. Determinism: identical call sequence ⇒ identical output.
